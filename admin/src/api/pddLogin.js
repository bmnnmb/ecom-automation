const PDD_SYSTEM_BASE = '/api/v1/system';

async function parsePddResponse(res, fallbackMessage) {
  const result = await res.json().catch(() => ({}));
  if (!res.ok || result.success === false) {
    throw new Error(result.detail || result.message || result.data?.message || fallbackMessage);
  }
  return result;
}

export async function startPddPasswordLogin() {
  const res = await fetch(`${PDD_SYSTEM_BASE}/pdd-login/start`, {
    method: 'POST',
    signal: AbortSignal.timeout(15000),
  });
  return parsePddResponse(res, '启动拼多多账号密码授权登录失败');
}

export async function fetchPddLoginStatus() {
  const res = await fetch(`${PDD_SYSTEM_BASE}/pdd-login/status`, {
    signal: AbortSignal.timeout(10000),
  });
  return parsePddResponse(res, '获取拼多多登录状态失败');
}

export async function cancelPddLogin() {
  const res = await fetch(`${PDD_SYSTEM_BASE}/pdd-login/cancel`, {
    method: 'POST',
    signal: AbortSignal.timeout(10000),
  });
  return parsePddResponse(res, '取消拼多多登录失败');
}
