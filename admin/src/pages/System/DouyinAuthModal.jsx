import React, { useState, useEffect } from 'react';
import { Modal, Steps, Button, message, Spin, Result, Image, Typography } from 'antd';
import {
  QrcodeOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  SyncOutlined
} from '@ant-design/icons';

const { Text } = Typography;

// 轮询配置常量
const POLL_INTERVAL_MS = 2000;      // 轮询间隔：2秒
const POLL_MAX_ATTEMPTS = 60;       // 最大轮询次数：60次（约2分钟）
const QR_LOAD_DELAY_MS = 2000;      // 二维码加载后延迟轮询时间
const SUCCESS_CLOSE_DELAY_MS = 1500; // 授权成功后关闭弹窗延迟

/**
 * 抖音扫码授权弹窗
 *
 * 授权流程：
 * 1. 发起登录 -> 获取二维码
 * 2. 展示二维码 -> 用户扫码
 * 3. 轮询状态 -> 检测是否登录成功
 * 4. 完成授权 -> 保存会话
 */
export default function DouyinAuthModal({ visible, onCancel, onSuccess }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [polling, setPolling] = useState(false);
  const [pollingTimer, setPollingTimer] = useState(null);
  const [loginStatus, setLoginStatus] = useState('pending'); // pending | success | failed | timeout

  // 使用相对路径，由 Vite proxy 转发到 pdd-cs-adapter (port 8003)
  const API_BASE = '';

  // 步骤配置
  const steps = [
    { title: '发起授权', icon: <QrcodeOutlined /> },
    { title: '扫码登录', icon: <LoadingOutlined /> },
    { title: '完成授权', icon: <CheckCircleOutlined /> },
  ];

  // 清理定时器
  useEffect(() => {
    return () => {
      if (pollingTimer) {
        clearInterval(pollingTimer);
      }
    };
  }, [pollingTimer]);

  // 重置状态
  const resetState = () => {
    setCurrentStep(0);
    setLoading(false);
    setQrCodeUrl('');
    setPolling(false);
    setLoginStatus('pending');
    if (pollingTimer) {
      clearInterval(pollingTimer);
      setPollingTimer(null);
    }
  };

  // 步骤1：发起扫码登录
  const startQrLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/system/douyin-login/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();

      if (result.success) {
        // 获取二维码截图
        const qrUrl = `${API_BASE}/api/v1/system/douyin-login/screenshot?t=${Date.now()}`;
        setQrCodeUrl(qrUrl);
        setCurrentStep(1);

        // 等待二维码加载后开始轮询
        setTimeout(() => {
          startPollingStatus();
        }, QR_LOAD_DELAY_MS);
      } else {
        throw new Error(result.message || '发起登录失败');
      }
    } catch (error) {
      message.error(`发起登录失败: ${error.message}`);
      setLoginStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  // 步骤2：轮询登录状态
  const startPollingStatus = () => {
    setPolling(true);
    let attemptCount = 0;

    const timer = setInterval(async () => {
      attemptCount++;

      try {
        const response = await fetch(`${API_BASE}/api/v1/system/douyin-login/status`);
        const result = await response.json();

        if (result.success && result.data) {
          const { is_logged_in, status } = result.data;

          if (is_logged_in) {
            // 登录成功，先停止轮询
            clearInterval(timer);
            setPolling(false);
            setLoginStatus('success');
            setCurrentStep(2);

            message.success('授权成功！');

            // 主动关闭后端浏览器，避免资源泄漏
            try {
              await fetch(`${API_BASE}/api/v1/system/douyin-login/cancel`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
              });
            } catch (error) {
              console.error('关闭浏览器失败:', error);
            }

            // 延迟后关闭弹窗并回调
            setTimeout(() => {
              onSuccess && onSuccess();
              handleCancel();
            }, SUCCESS_CLOSE_DELAY_MS);
          } else if (status === 'failed') {
            // 登录失败
            clearInterval(timer);
            setPolling(false);
            setLoginStatus('failed');
            message.error('登录失败，请重试');
          } else if (attemptCount >= POLL_MAX_ATTEMPTS) {
            // 超时
            clearInterval(timer);
            setPolling(false);
            setLoginStatus('timeout');
            message.warning('登录超时，请重新发起授权');
          }
        }
      } catch (error) {
        console.error('轮询状态失败:', error);
        // 继续轮询，不中断
      }
    }, POLL_INTERVAL_MS);

    setPollingTimer(timer);
  };

  // 取消授权
  const cancelAuth = async () => {
    try {
      await fetch(`${API_BASE}/api/v1/system/douyin-login/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      console.error('取消授权失败:', error);
    }
  };

  // 关闭弹窗
  const handleCancel = () => {
    if (polling) {
      cancelAuth();
    }
    resetState();
    onCancel && onCancel();
  };

  // 重试
  const handleRetry = () => {
    resetState();
    startQrLogin();
  };

  // 渲染步骤内容
  const renderStepContent = () => {
    // 步骤1：发起授权
    if (currentStep === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          {loginStatus === 'failed' ? (
            <Result
              status="error"
              title="授权失败"
              subTitle="发起登录失败，请检查网络连接或稍后重试"
              extra={[
                <Button key="retry" type="primary" onClick={handleRetry}>
                  重新授权
                </Button>,
                <Button key="cancel" onClick={handleCancel}>
                  取消
                </Button>
              ]}
            />
          ) : (
            <>
              <QrcodeOutlined style={{ fontSize: 64, color: '#165DFF', marginBottom: 24 }} />
              <div style={{ marginBottom: 32 }}>
                <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
                  准备发起抖音商家授权
                </div>
                <Text type="secondary">
                  点击下方按钮后，将打开登录浏览器并生成二维码
                </Text>
              </div>
              <Button
                type="primary"
                size="large"
                loading={loading}
                onClick={startQrLogin}
                style={{ width: 200, height: 48, fontSize: 16 }}
              >
                {loading ? '正在生成二维码...' : '开始授权'}
              </Button>
            </>
          )}
        </div>
      );
    }

    // 步骤2：扫码登录
    if (currentStep === 1) {
      if (loginStatus === 'timeout') {
        return (
          <Result
            status="warning"
            title="登录超时"
            subTitle="您在2分钟内未完成扫码，请重新发起授权"
            extra={[
              <Button key="retry" type="primary" onClick={handleRetry}>
                重新授权
              </Button>,
              <Button key="cancel" onClick={handleCancel}>
                取消
              </Button>
            ]}
          />
        );
      }

      return (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
              请使用抖音APP扫码
            </div>
            <Text type="secondary">
              打开抖音APP扫码；如出现滑块，请在弹出的浏览器窗口中拖动完成验证
            </Text>
          </div>

          {qrCodeUrl ? (
            <div style={{
              display: 'inline-block',
              padding: 16,
              background: '#fff',
              borderRadius: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}>
              <Image
                src={qrCodeUrl}
                alt="抖音登录二维码"
                width={280}
                height={280}
                preview={false}
                placeholder={
                  <div style={{ width: 280, height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Spin size="large" />
                  </div>
                }
              />
            </div>
          ) : (
            <div style={{
              width: 312,
              height: 312,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#fafafa',
              borderRadius: 8
            }}>
              <Spin size="large" tip="正在加载二维码..." />
            </div>
          )}

          {polling && (
            <div style={{ marginTop: 24 }}>
              <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
              <div style={{ marginTop: 12 }}>
                <Text type="secondary">等待扫码确认...</Text>
              </div>
            </div>
          )}

          <div style={{ marginTop: 32 }}>
            <Button onClick={handleCancel} disabled={loading}>
              取消授权
            </Button>
            <Button
              type="link"
              icon={<SyncOutlined />}
              onClick={handleRetry}
              style={{ marginLeft: 16 }}
            >
              刷新二维码
            </Button>
          </div>
        </div>
      );
    }

    // 步骤3：完成授权
    if (currentStep === 2) {
      return (
        <Result
          status="success"
          title="授权成功！"
          subTitle="抖音商家账号已成功授权，可以开始使用自动化功能"
          extra={[
            <Button key="done" type="primary" onClick={handleCancel}>
              完成
            </Button>
          ]}
        />
      );
    }
  };

  return (
    <Modal
      title="抖音店铺授权"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={600}
      centered
      maskClosable={false}
      destroyOnClose
    >
      <Steps
        current={currentStep}
        items={steps}
        style={{ marginBottom: 32 }}
      />

      {renderStepContent()}
    </Modal>
  );
}
