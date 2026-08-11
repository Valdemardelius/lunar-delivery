const BASE = '/api';

async function request(path, options) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.detail || 'Ошибка запроса');
    err.status = res.status;
    throw err;
  }
  return data;
}

export const api = {
  getState: () => request('/state'),
  send: (orderId, roverId) =>
    request('/send', { method: 'POST', body: JSON.stringify({ order_id: orderId, rover_id: roverId }) }),
  repair: (roverId) =>
    request('/repair', { method: 'POST', body: JSON.stringify({ rover_id: roverId }) }),
  advanceDay: () => request('/advance_day', { method: 'POST' }),
  reset: () => request('/reset', { method: 'POST' }),
};