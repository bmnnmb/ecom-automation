/**
 * 系统设置
 * 店铺信息 + 平台配置 + 通知设置 + AI配置
 *
 * 真实API版本: GET/PUT /api/settings
 * 后端不可用时降级使用 localStorage
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  fetchSettings,
  saveSettings,
} from '../../api/index.js';
import {
  startPddPasswordLogin,
  fetchPddLoginStatus,
  cancelPddLogin,
} from '../../api/pddLogin.js';
import { DEFAULT_SETTINGS, PLATFORMS } from '../../utils/mock';
import '../Competitors/Competitors.css';

export default function Settings() {
  const [settings, setSettings] = useState(null);
  const [activeTab, setActiveTab] = useState('general');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saveStatus, setSaveStatus] = useState(null); // 'success' | 'error' | null
  const [dataSource, setDataSource] = useState(null);  // 'api' | 'local' | null
  const [douyinConnected, setDouyinConnected] = useState(!!localStorage.getItem('douyin_token'));
  const [hasChanges, setHasChanges] = useState(false);
  const [pddLoginLoading, setPddLoginLoading] = useState(false);
  const [pddLoginPolling, setPddLoginPolling] = useState(false);
  const [pddLoginStatus, setPddLoginStatus] = useState('idle');
  const [pddAuthInfoUrl, setPddAuthInfoUrl] = useState('/api/v1/system/pdd-auth/page');
  const [pddBrowserControlUrl, setPddBrowserControlUrl] = useState('');
  const [pddLoginMessage, setPddLoginMessage] = useState('用于本地客服工作台自动化，不是开放平台授权');

  // 初始化: 从后端加载配置
  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const result = await fetchSettings();
        if (result && result.data) {
          setSettings(result.data);
          setDataSource(result.source);
        } else {
          // 后端不可用且无本地备份，使用默认值
          setSettings(DEFAULT_SETTINGS);
          setDataSource('default');
        }
      } catch (e) {
        console.error('加载设置失败:', e);
        setSettings(DEFAULT_SETTINGS);
        setDataSource('default');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleDouyinAuth = async () => {
    const redirectUri = window.location.origin + '/settings?auth=callback';
    try {
      const res = await fetch(`http://localhost:8001/auth/url?redirect_uri=${encodeURIComponent(redirectUri)}`);
      const data = await res.json();
      if (data?.data?.auth_url) {
        window.open(data.data.auth_url, '_blank');
      } else {
        alert('请先启动后端服务 (端口8001) 并配置 DOUYIN_APP_KEY');
      }
    } catch {
      alert('无法连接后端服务，请确保 douyin-adapter 服务已启动\n\n启动命令:\ncd ~/ecom-automation/services/douyin-adapter && pip install -r requirements.txt && python main.py');
    }
  };

  const updateSetting = (section, key, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: { ...prev[section], [key]: value }
    }));
    setHasChanges(true);
    setSaveStatus(null);
  };

  const handleSave = useCallback(async () => {
    if (!settings || saving) return;
    setSaving(true);
    setSaveStatus(null);
    try {
      const result = await saveSettings(settings);
      setDataSource(result.source);
      setSaveStatus('success');
      setHasChanges(false);
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (e) {
      console.error('保存设置失败:', e);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus(null), 5000);
    } finally {
      setSaving(false);
    }
  }, [settings, saving]);

  const handleStartPddPasswordLogin = useCallback(async () => {
    setPddLoginLoading(true);
    setPddLoginStatus('idle');
    try {
      const result = await startPddPasswordLogin();
      setPddAuthInfoUrl(result.data?.auth_info_url || '/api/v1/system/pdd-auth/page');
      setPddBrowserControlUrl(result.data?.browser_control_url || '');
      setPddLoginMessage(result.message || '已打开浏览器并填入账号密码，请完成必要验证');
      setPddLoginStatus('waiting');
      setPddLoginPolling(true);
    } catch (e) {
      console.error('启动拼多多账号密码授权登录失败:', e);
      setPddLoginStatus('error');
      setPddLoginMessage(e.message || '启动拼多多账号密码授权登录失败');
      setPddLoginPolling(false);
    } finally {
      setPddLoginLoading(false);
    }
  }, []);

  const handleCancelPddLogin = useCallback(async () => {
    try {
      await cancelPddLogin();
    } catch (e) {
      console.error('取消拼多多登录失败:', e);
    } finally {
      setPddLoginPolling(false);
      setPddLoginStatus('idle');
      setPddLoginMessage('用于本地客服工作台自动化，不是开放平台授权');
      setPddAuthInfoUrl('/api/v1/system/pdd-auth/page');
      setPddBrowserControlUrl('');
    }
  }, []);

  useEffect(() => {
    if (!pddLoginPolling) return undefined;

    const timer = setInterval(async () => {
      try {
        const status = await fetchPddLoginStatus();
        const data = status.data || {};
        if (data.is_logged_in) {
          setPddLoginStatus('success');
          setPddLoginMessage(data.message || '拼多多商家后台已授权');
          setPddLoginPolling(false);
          return;
        }

        if (data.status === 'closed' || data.status === 'failed') {
          setPddLoginStatus('error');
          setPddLoginMessage(data.message || '未检测到有效授权');
          setPddLoginPolling(false);
          return;
        }

        setPddLoginStatus('waiting');
        setPddLoginMessage(data.message || '等待账号密码登录完成');
      } catch (e) {
        console.error('检查拼多多登录状态失败:', e);
        setPddLoginStatus('error');
        setPddLoginMessage(e.message || '检查拼多多登录状态失败');
        setPddLoginPolling(false);
      }
    }, 3000);

    return () => clearInterval(timer);
  }, [pddLoginPolling]);

  const tabs = [
    { key: 'general', label: '基础设置', icon: '⚙️' },
    { key: 'platforms', label: '平台配置', icon: '🔗' },
    { key: 'douyin', label: '抖音对接', icon: '🎵' },
    { key: 'notifications', label: '通知设置', icon: '🔔' },
    { key: 'ai', label: 'AI 配置', icon: '🤖' },
  ];

  // Switch 组件
  const Switch = ({ checked, onChange }) => (
    <div className={`switch ${checked ? 'on' : ''}`} onClick={() => onChange(!checked)} />
  );

  // 加载中
  if (loading || !settings) {
    return (
      <div className="fade-in">
        <div className="page-header">
          <h2 className="page-title">系统设置</h2>
          <p className="page-desc">加载中...</p>
        </div>
        <div className="card">
          <div className="card-body" style={{ textAlign: 'center', padding: 60, color: 'var(--text-3)' }}>
            ⏳ 正在加载配置...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 className="page-title">系统设置</h2>
            <p className="page-desc">管理店铺信息、平台对接、通知和AI配置</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {dataSource && (
              <span style={{
                fontSize: 12,
                padding: '4px 10px',
                borderRadius: 12,
                background: dataSource === 'api' ? '#E8FFEA' : dataSource === 'local' ? '#FFF7E8' : '#F2F3F5',
                color: dataSource === 'api' ? '#00B42A' : dataSource === 'local' ? '#D46B08' : '#86909C',
              }}>
                {dataSource === 'api' ? '🟢 后端已连接' : dataSource === 'local' ? '🟡 本地存储' : '⚪ 使用默认值'}
              </span>
            )}
            {hasChanges && (
              <span style={{ fontSize: 12, color: '#FF7D00' }}>● 有未保存的更改</span>
            )}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 'var(--spacing-lg)' }}>
        {/* 左侧导航 */}
        <div className="card" style={{ height: 'fit-content' }}>
          <div className="card-body" style={{ padding: 'var(--spacing-sm)' }}>
            {tabs.map(tab => (
              <div
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 14px',
                  borderRadius: 6,
                  cursor: 'pointer',
                  marginBottom: 2,
                  background: activeTab === tab.key ? 'var(--primary-light)' : 'transparent',
                  color: activeTab === tab.key ? 'var(--primary)' : 'var(--text-2)',
                  fontWeight: activeTab === tab.key ? 500 : 400,
                  transition: 'all 0.2s',
                }}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 右侧内容 */}
        <div className="card">
          <div className="card-body">
            {/* 基础设置 */}
            {activeTab === 'general' && (
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>基础设置</h3>
                <div className="form-group">
                  <label className="form-label">店铺名称</label>
                  <input
                    className="form-input"
                    value={settings.general.shopName}
                    onChange={e => updateSetting('general', 'shopName', e.target.value)}
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                  <div className="form-group">
                    <label className="form-label">联系电话</label>
                    <input
                      className="form-input"
                      value={settings.general.contactPhone}
                      onChange={e => updateSetting('general', 'contactPhone', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">联系邮箱</label>
                    <input
                      className="form-input"
                      value={settings.general.contactEmail}
                      onChange={e => updateSetting('general', 'contactEmail', e.target.value)}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">自动回复</label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <Switch
                      checked={settings.general.autoReply}
                      onChange={v => updateSetting('general', 'autoReply', v)}
                    />
                    <span style={{ fontSize: 13, color: 'var(--text-3)' }}>
                      开启后自动回复客户常见问题
                    </span>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">系统语言</label>
                  <select
                    className="form-input"
                    value={settings.general.language}
                    onChange={e => updateSetting('general', 'language', e.target.value)}
                  >
                    <option value="zh-CN">简体中文</option>
                    <option value="en-US">English</option>
                  </select>
                </div>
              </div>
            )}

            {/* 平台配置 */}
            {activeTab === 'platforms' && (
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>平台配置</h3>
                {PLATFORMS.map(plat => {
                  const config = settings.platforms[plat.key] || {};
                  return (
                    <div key={plat.key} style={{
                      padding: 20,
                      border: '1px solid var(--border)',
                      borderRadius: 8,
                      marginBottom: 16,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <span style={{ fontSize: 24 }}>{plat.icon}</span>
                          <div>
                            <div style={{ fontWeight: 600 }}>{plat.name}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
                              {config.enabled ? '已启用' : '未启用'}
                            </div>
                          </div>
                        </div>
                        <Switch
                          checked={config.enabled}
                          onChange={v => updateSetting('platforms', plat.key, { ...config, enabled: v })}
                        />
                      </div>
                      {config.enabled && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                          <div className="form-group" style={{ marginBottom: 0 }}>
                            <label className="form-label" style={{ fontSize: 13 }}>App ID</label>
                            <input
                              className="form-input"
                              placeholder="输入应用ID"
                              value={config.appId || ''}
                              onChange={e => updateSetting('platforms', plat.key, { ...config, appId: e.target.value })}
                            />
                          </div>
                          <div className="form-group" style={{ marginBottom: 0 }}>
                            <label className="form-label" style={{ fontSize: 13 }}>同步间隔</label>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <input
                                className="form-input"
                                type="number"
                                min={5}
                                value={config.syncInterval || 15}
                                onChange={e => updateSetting('platforms', plat.key, { ...config, syncInterval: +e.target.value })}
                                style={{ width: 80 }}
                              />
                              <span style={{ fontSize: 13, color: 'var(--text-3)' }}>分钟</span>
                              <Switch
                                checked={config.autoSync}
                                onChange={v => updateSetting('platforms', plat.key, { ...config, autoSync: v })}
                              />
                              <span style={{ fontSize: 13, color: 'var(--text-3)' }}>自动同步</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}

                <div style={{
                  padding: 20,
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  background: 'var(--bg-2)',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, marginBottom: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{
                        width: 44,
                        height: 44,
                        borderRadius: 12,
                        background: '#E02E24',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 20,
                        color: '#fff',
                      }}>
                        多
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 16 }}>拼多多账号密码授权</div>
                        <div style={{ fontSize: 13, color: 'var(--text-3)', marginTop: 4 }}>
                          后端从 .env 自动填入账号密码；滑块、短信等验证由用户手动完成
                        </div>
                      </div>
                    </div>
                    <span style={{
                      fontSize: 12,
                      padding: '4px 10px',
                      borderRadius: 12,
                      background: pddLoginStatus === 'success' ? '#E8FFEA' : pddLoginStatus === 'error' ? '#FFF1F0' : '#F2F3F5',
                      color: pddLoginStatus === 'success' ? '#00B42A' : pddLoginStatus === 'error' ? '#F53F3F' : '#86909C',
                    }}>
                      {pddLoginStatus === 'success' ? '已授权' : pddLoginStatus === 'error' ? '登录异常' : pddLoginPolling ? '等待登录' : '未启动'}
                    </span>
                  </div>

                  <div style={{
                    padding: '14px 16px',
                    background: pddLoginStatus === 'error' ? '#FFF1F0' : pddLoginStatus === 'success' ? '#F6FFED' : '#F7F8FA',
                    border: `1px solid ${pddLoginStatus === 'error' ? '#FFCCC7' : pddLoginStatus === 'success' ? '#B7EB8F' : 'var(--border)'}`,
                    borderRadius: 8,
                    color: pddLoginStatus === 'error' ? '#CF1322' : 'var(--text-2)',
                    marginBottom: 16,
                    lineHeight: 1.6,
                  }}>
                    {pddLoginMessage}
                  </div>

                  {pddAuthInfoUrl && (
                    <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                      {pddBrowserControlUrl && (
                        <a href={pddBrowserControlUrl} target="_blank" rel="noreferrer" style={{ fontSize: 13 }}>
                          打开远程浏览器
                        </a>
                      )}
                      <a href={pddAuthInfoUrl} target="_blank" rel="noreferrer" style={{ fontSize: 13 }}>
                        查看拼多多授权信息
                      </a>
                    </div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                    <button
                      className="btn btn-primary"
                      onClick={handleStartPddPasswordLogin}
                      disabled={pddLoginLoading}
                      style={{ minWidth: 132 }}
                    >
                      {pddLoginLoading ? '正在启动...' : pddLoginPolling ? '重新发起授权' : '账号密码授权'}
                    </button>
                    {pddLoginPolling && (
                      <button className="btn btn-default" onClick={handleCancelPddLogin}>
                        取消
                      </button>
                    )}
                    {pddLoginPolling && (
                      <span style={{ fontSize: 13, color: 'var(--text-3)' }}>
                        每 3 秒自动检查一次登录状态
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* 抖音对接 */}
            {activeTab === 'douyin' && (
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>🎵 抖音店铺对接</h3>
                
                {/* 连接状态 */}
                <div style={{
                  padding: 20, border: '1px solid var(--border)', borderRadius: 8, marginBottom: 20,
                  background: 'var(--bg-2)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                    <div style={{
                      width: 48, height: 48, borderRadius: 12, background: '#FE2C55',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
                    }}>🎵</div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 16 }}>抖音开放平台</div>
                      <div style={{ fontSize: 13, color: 'var(--text-3)' }}>
                        {douyinConnected ? '✅ 已连接店铺' : '⚠️ 未连接'}
                      </div>
                    </div>
                    <div style={{ marginLeft: 'auto' }}>
                      {douyinConnected ? (
                        <button className="btn btn-default btn-sm" onClick={() => { setDouyinConnected(false); localStorage.removeItem('douyin_token'); }}>
                          断开连接
                        </button>
                      ) : (
                        <button className="btn btn-primary" onClick={handleDouyinAuth}>
                          🔗 连接抖音店铺
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {!douyinConnected && (
                    <div style={{ padding: '16px', background: '#FFF7E8', borderRadius: 8, border: '1px solid #FFD591' }}>
                      <div style={{ fontWeight: 500, marginBottom: 8, color: '#D46B08' }}>⚠️ 需要先配置应用信息</div>
                      <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.8 }}>
                        1. 前往 <a href="https://developer.open-douyin.com" target="_blank" style={{ color: 'var(--primary)' }}>抖音开放平台</a> 创建应用<br/>
                        2. 获取 App Key 和 App Secret<br/>
                        3. 在后端设置环境变量 DOUYIN_APP_KEY 和 DOUYIN_APP_SECRET<br/>
                        4. 点击上方"连接抖音店铺"按钮进行授权
                      </div>
                    </div>
                  )}
                </div>

                {/* API配置 */}
                <div className="form-group">
                  <label className="form-label">App Key</label>
                  <input
                    className="form-input"
                    placeholder="输入抖音应用App Key"
                    value={settings.douyin?.appKey || ''}
                    onChange={e => updateSetting('douyin', 'appKey', e.target.value)}
                  />
                  <div className="form-hint">在抖音开放平台 → 管理中心 → 应用详情 中获取</div>
                </div>
                <div className="form-group">
                  <label className="form-label">App Secret</label>
                  <input
                    className="form-input"
                    type="password"
                    placeholder="输入抖音应用App Secret"
                    value={settings.douyin?.appSecret || ''}
                    onChange={e => updateSetting('douyin', 'appSecret', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">后端API地址</label>
                  <input
                    className="form-input"
                    placeholder="后端服务地址"
                    value={settings.douyin?.apiUrl || 'http://localhost:8001'}
                    onChange={e => updateSetting('douyin', 'apiUrl', e.target.value)}
                  />
                  <div className="form-hint">抖店Adapter服务的地址，默认 http://localhost:8001</div>
                </div>

                {/* API权限 */}
                <div style={{ marginTop: 20 }}>
                  <div style={{ fontWeight: 500, marginBottom: 12 }}>需要的API权限</div>
                  {[
                    { name: '商品管理', api: 'product.*', status: '待授权' },
                    { name: '订单管理', api: 'order.*', status: '待授权' },
                    { name: '物流管理', api: 'logistics.*', status: '待授权' },
                    { name: '售后管理', api: 'aftersale.*', status: '待授权' },
                    { name: '客服消息', api: 'im.*', status: '待授权' },
                    { name: '数据罗盘', api: 'data.*', status: '待授权' },
                  ].map((item, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', padding: '10px 0',
                      borderBottom: '1px solid var(--border)',
                    }}>
                      <span style={{ width: 100, fontWeight: 500 }}>{item.name}</span>
                      <code style={{ flex: 1, fontSize: 12, color: 'var(--text-3)', background: 'var(--bg-3)', padding: '2px 8px', borderRadius: 4 }}>{item.api}</code>
                      <span className="tag tag-orange">{item.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 通知设置 */}
            {activeTab === 'notifications' && (
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>通知设置</h3>
                {[
                  { key: 'orderAlert', label: '新订单提醒', desc: '收到新订单时通知' },
                  { key: 'refundAlert', label: '退款申请提醒', desc: '客户发起退款时通知' },
                  { key: 'stockAlert', label: '库存预警提醒', desc: '库存低于安全阈值时通知' },
                  { key: 'competitorAlert', label: '竞品价格变动提醒', desc: '竞品价格发生较大变动时通知' },
                  { key: 'dailyReport', label: '每日数据报告', desc: '每天推送运营数据汇总' },
                ].map(item => (
                  <div key={item.key} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '16px 0',
                    borderBottom: '1px solid var(--border)',
                  }}>
                    <div>
                      <div style={{ fontWeight: 500, marginBottom: 4 }}>{item.label}</div>
                      <div style={{ fontSize: 13, color: 'var(--text-3)' }}>{item.desc}</div>
                    </div>
                    <Switch
                      checked={settings.notifications[item.key]}
                      onChange={v => updateSetting('notifications', item.key, v)}
                    />
                  </div>
                ))}
                <div style={{ marginTop: 20 }}>
                  <div className="form-group">
                    <label className="form-label">通知渠道</label>
                    <select
                      className="form-input"
                      value={settings.notifications.alertChannel}
                      onChange={e => updateSetting('notifications', 'alertChannel', e.target.value)}
                    >
                      <option value="feishu">飞书</option>
                      <option value="wechat">微信</option>
                      <option value="email">邮件</option>
                      <option value="sms">短信</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* AI 配置 */}
            {activeTab === 'ai' && (
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>AI 配置</h3>
                {[
                  { key: 'autoCustomerService', label: 'AI自动客服', desc: '自动回复客户常见问题' },
                  { key: 'autoProductDescription', label: 'AI商品描述', desc: '自动生成商品标题和详情' },
                  { key: 'autoPricing', label: 'AI智能定价', desc: '根据竞品数据自动调整价格' },
                ].map(item => (
                  <div key={item.key} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '16px 0',
                    borderBottom: '1px solid var(--border)',
                  }}>
                    <div>
                      <div style={{ fontWeight: 500, marginBottom: 4 }}>{item.label}</div>
                      <div style={{ fontSize: 13, color: 'var(--text-3)' }}>{item.desc}</div>
                    </div>
                    <Switch
                      checked={settings.ai[item.key]}
                      onChange={v => updateSetting('ai', item.key, v)}
                    />
                  </div>
                ))}
                <div style={{ marginTop: 20 }}>
                  <div className="form-group">
                    <label className="form-label">AI 模型</label>
                    <select
                      className="form-input"
                      value={settings.ai.model}
                      onChange={e => updateSetting('ai', 'model', e.target.value)}
                    >
                      <option value="gpt-4">GPT-4 (推荐)</option>
                      <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                      <option value="claude-3">Claude 3</option>
                      <option value="qwen">通义千问</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">
                      置信度阈值: {(settings.ai.confidenceThreshold * 100).toFixed(0)}%
                    </label>
                    <input
                      type="range"
                      min={50}
                      max={100}
                      value={settings.ai.confidenceThreshold * 100}
                      onChange={e => updateSetting('ai', 'confidenceThreshold', e.target.value / 100)}
                      style={{ width: '100%' }}
                    />
                    <div className="form-hint">低于此置信度时，AI会转人工处理</div>
                  </div>
                </div>
              </div>
            )}

            {/* 保存按钮 */}
            <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 16 }}>
              <button
                className={`btn ${saveStatus === 'success' ? 'btn-default' : 'btn-primary'}`}
                onClick={handleSave}
                disabled={saving || !hasChanges}
                style={{
                  minWidth: 120,
                  opacity: (!hasChanges && !saving) ? 0.6 : 1,
                  cursor: (!hasChanges && !saving) ? 'not-allowed' : 'pointer',
                }}
              >
                {saving ? '⏳ 保存中...' : saveStatus === 'success' ? '✅ 已保存' : saveStatus === 'error' ? '❌ 保存失败' : '💾 保存设置'}
              </button>
              {saveStatus === 'success' && (
                <span style={{ fontSize: 13, color: '#00B42A' }}>
                  配置已保存到{dataSource === 'api' ? '服务器' : '本地存储'}
                </span>
              )}
              {saveStatus === 'error' && (
                <span style={{ fontSize: 13, color: '#F53F3F' }}>
                  保存失败，请检查网络连接后重试
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
