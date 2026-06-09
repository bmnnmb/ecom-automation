const PDD_SYSTEM_BASE = '/api/v1/system';

export async function startPddQrLogin() {
  const res = await fetch(`${PDD_SYSTEM_BASE}/pdd-login/start`, {
    method: 'POST',
    signal: AbortSignal.timeout(15000),
  });
  if (!res.ok) throw new Error('启动拼多多扫码登录失败');
  return res.json();
}

export async function fetchPddQrLoginStatus() {
  const res = await fetch(`${PDD_SYSTEM_BASE}/pdd-login/status`, {
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) throw new Error('获取拼多多登录状态失败');
  return res.json();
}

export async function cancelPddQrLogin() {
  const res = await fetch(`${PDD_SYSTEM_BASE}/pdd-login/cancel`, {
    method: 'POST',
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) throw new Error('取消拼多多扫码登录失败');
  return res.json();
}
