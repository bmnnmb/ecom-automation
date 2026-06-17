import React, { useEffect, useRef, useState } from 'react';
import { Modal, Steps, Button, message, Spin, Result, Typography, Alert, Space } from 'antd';
import {
  LoginOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

const POLL_INTERVAL_MS = 2000;
const POLL_MAX_ATTEMPTS = 150;
const SUCCESS_CLOSE_DELAY_MS = 1500;

async function parseApiResponse(response, fallbackMessage) {
  const result = await response.json().catch(() => ({}));
  if (!response.ok || result.success === false) {
    throw new Error(result.detail || result.message || result.data?.message || fallbackMessage);
  }
  return result;
}

export default function PddAuthModal({ visible, onCancel, onSuccess }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [loginStatus, setLoginStatus] = useState('pending');
  const [errorDetail, setErrorDetail] = useState('');
  const [authInfoUrl, setAuthInfoUrl] = useState('/api/v1/system/pdd-auth/page');
  const [browserControlUrl, setBrowserControlUrl] = useState('');
  const pollingTimerRef = useRef(null);

  const steps = [
    { title: '发起授权', icon: <LoginOutlined /> },
    { title: '完成验证', icon: <LoadingOutlined /> },
    { title: '完成授权', icon: <CheckCircleOutlined /> },
  ];

  const clearPolling = () => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
    setPolling(false);
  };

  const resetState = () => {
    clearPolling();
    setCurrentStep(0);
    setLoading(false);
    setLoginStatus('pending');
    setErrorDetail('');
    setAuthInfoUrl('/api/v1/system/pdd-auth/page');
    setBrowserControlUrl('');
  };

  useEffect(() => {
    return () => clearPolling();
  }, []);

  const checkLoginStatus = async () => {
    const response = await fetch('/api/v1/system/pdd-login/status');
    const result = await parseApiResponse(response, '获取拼多多登录状态失败');
    const data = result.data || {};

    if (data.is_logged_in) {
      clearPolling();
      setLoginStatus('success');
      setCurrentStep(2);
      message.success(data.message || '拼多多授权成功');

      setTimeout(() => {
        onSuccess && onSuccess();
        handleCancel(false);
      }, SUCCESS_CLOSE_DELAY_MS);
      return true;
    }

    if (data.status === 'closed' || data.status === 'failed') {
      clearPolling();
      setLoginStatus('failed');
      setErrorDetail(data.message || '未检测到有效授权，请重新发起');
      return true;
    }

    return false;
  };

  const startPollingStatus = () => {
    clearPolling();
    setPolling(true);
    let attemptCount = 0;

    pollingTimerRef.current = setInterval(async () => {
      attemptCount += 1;

      try {
        const finished = await checkLoginStatus();
        if (!finished && attemptCount >= POLL_MAX_ATTEMPTS) {
          clearPolling();
          setLoginStatus('timeout');
          setErrorDetail('授权检测超时，请确认是否已在浏览器中完成登录');
        }
      } catch (error) {
        console.error('轮询状态失败:', error);
      }
    }, POLL_INTERVAL_MS);
  };

  const startPasswordLogin = async () => {
    setLoading(true);
    setErrorDetail('');

    try {
      const response = await fetch('/api/v1/system/pdd-login/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const result = await parseApiResponse(response, '启动拼多多账号密码授权登录失败');

      setAuthInfoUrl(result.data?.auth_info_url || '/api/v1/system/pdd-auth/page');
      setBrowserControlUrl(result.data?.browser_control_url || '');
      setCurrentStep(1);
      setLoginStatus('waiting');
      message.success(result.message || '已打开浏览器并填入账号密码');
      startPollingStatus();
    } catch (error) {
      setLoginStatus('failed');
      setErrorDetail(error.message);
      message.error(`发起授权失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const cancelAuth = async () => {
    try {
      await fetch('/api/v1/system/pdd-login/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
    } catch (error) {
      console.error('取消授权失败:', error);
    }
  };

  const handleCancel = (shouldCancelRemote = true) => {
    if (shouldCancelRemote && (polling || currentStep === 1)) {
      cancelAuth();
    }
    resetState();
    onCancel && onCancel();
  };

  const handleRetry = () => {
    resetState();
    startPasswordLogin();
  };

  const renderStepContent = () => {
    if (currentStep === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          {loginStatus === 'failed' ? (
            <Result
              status="error"
              title="授权启动失败"
              subTitle={errorDetail || '无法打开拼多多登录页面'}
              extra={[
                <Button key="retry" type="primary" onClick={handleRetry}>
                  重新授权
                </Button>,
                <Button key="cancel" onClick={() => handleCancel(false)}>
                  取消
                </Button>,
              ]}
            />
          ) : (
            <>
              <SafetyCertificateOutlined style={{ fontSize: 64, color: '#165DFF', marginBottom: 24 }} />
              <div style={{ marginBottom: 32 }}>
                <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
                  拼多多店铺授权
                </div>
                <Text type="secondary">
                  后端会从 .env 自动填入账号密码；滑块、短信等验证由用户手动完成。
                </Text>
              </div>
              <Button
                type="primary"
                size="large"
                icon={<LoginOutlined />}
                loading={loading}
                onClick={startPasswordLogin}
                style={{ minWidth: 180, height: 48, fontSize: 16 }}
              >
                {loading ? '正在启动...' : '账号密码授权'}
              </Button>
            </>
          )}
        </div>
      );
    }

    if (currentStep === 1) {
      if (loginStatus === 'timeout' || loginStatus === 'failed') {
        return (
          <Result
            status={loginStatus === 'timeout' ? 'warning' : 'error'}
            title={loginStatus === 'timeout' ? '授权检测超时' : '授权未完成'}
            subTitle={errorDetail || '请重新发起授权并完成必要验证'}
            extra={[
              <Button key="retry" type="primary" onClick={handleRetry}>
                重新授权
              </Button>,
              <Button key="cancel" onClick={() => handleCancel(false)}>
                取消
              </Button>,
            ]}
          />
        );
      }

      return (
        <div style={{ padding: '20px 0' }}>
          <Alert
            type="info"
            showIcon
            message={browserControlUrl ? '请打开远程浏览器完成验证' : '请在打开的拼多多商家后台页面完成验证'}
            description="系统已自动填入 .env 中的账号密码；如果出现滑块、短信或扫码确认，请手动完成。检测到有效登录态后会保存 session 并关闭浏览器。"
            style={{ marginBottom: 24 }}
          />

          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            {polling && (
              <>
                <Spin indicator={<LoadingOutlined style={{ fontSize: 28 }} spin />} />
                <div style={{ marginTop: 12 }}>
                  <Text type="secondary">正在检测账号密码授权状态...</Text>
                </div>
              </>
            )}
          </div>

          <Space style={{ display: 'flex', justifyContent: 'center' }}>
            <Button
              type="primary"
              icon={<SyncOutlined />}
              onClick={checkLoginStatus}
              disabled={loading}
            >
              立即检测
            </Button>
            {browserControlUrl && (
              <Button href={browserControlUrl} target="_blank">
                打开远程浏览器
              </Button>
            )}
            <Button href={authInfoUrl} target="_blank">
              查看授权信息
            </Button>
            <Button onClick={() => handleCancel()} disabled={loading}>
              取消授权
            </Button>
          </Space>
        </div>
      );
    }

    return (
      <Result
        status="success"
        title="授权成功"
        subTitle="拼多多商家账号 session 已保存，可以开始使用自动化功能。"
        extra={[
          <Button key="done" type="primary" onClick={() => handleCancel(false)}>
            完成
          </Button>,
        ]}
      />
    );
  };

  return (
    <Modal
      title="拼多多店铺授权"
      open={visible}
      onCancel={() => handleCancel()}
      footer={null}
      width={600}
      centered
      maskClosable={false}
      destroyOnClose
    >
      <Steps current={currentStep} items={steps} style={{ marginBottom: 32 }} />
      {renderStepContent()}
    </Modal>
  );
}
