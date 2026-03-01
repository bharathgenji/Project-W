const BASE = '/api';

async function request(url, options = {}) {
  const response = await fetch(`${BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error ${response.status}: ${errorBody}`);
  }

  return response.json();
}

// --------------- Leads ---------------

export function getLeads({
  trade,
  state,
  city,
  zip,
  min_value,
  max_value,
  posted_after,
  status,
  sort_by = 'score',
  limit = 20,
  offset = 0,
} = {}) {
  const params = new URLSearchParams();
  if (trade) params.set('trade', trade);
  if (state) params.set('state', state);
  if (city) params.set('city', city);
  if (zip) params.set('zip', zip);
  if (min_value) params.set('min_value', min_value);
  if (max_value) params.set('max_value', max_value);
  if (posted_after) params.set('posted_after', posted_after);
  if (status) params.set('status', status);
  if (sort_by) params.set('sort_by', sort_by);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return request(`/leads?${params.toString()}`);
}

export function getLead(leadId) {
  return request(`/leads/${encodeURIComponent(leadId)}`);
}

// --------------- Search ---------------

export function searchLeads(q, limit = 20) {
  const params = new URLSearchParams({ q, limit: String(limit) });
  return request(`/search?${params.toString()}`);
}

// --------------- Contractors ---------------

export function getContractors({
  trade,
  state,
  license_status,
  limit = 20,
  offset = 0,
} = {}) {
  const params = new URLSearchParams();
  if (trade) params.set('trade', trade);
  if (state) params.set('state', state);
  if (license_status) params.set('license_status', license_status);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return request(`/contractors?${params.toString()}`);
}

export function getContractor(contractorId) {
  return request(`/contractors/${encodeURIComponent(contractorId)}`);
}

// --------------- Dashboard ---------------

export function getDashboard() {
  return request('/dashboard');
}

// --------------- Markets ---------------

export function getMarket(state) {
  return request(`/markets/${encodeURIComponent(state)}`);
}

// --------------- Alerts ---------------

export function createAlert({ email, trade, state, city, min_value, max_value }) {
  return request('/alerts', {
    method: 'POST',
    body: JSON.stringify({ email, trade, state, city, min_value, max_value }),
  });
}

export function getAlerts(email) {
  const params = new URLSearchParams();
  if (email) params.set('email', email);
  return request(`/alerts?${params.toString()}`);
}

export function deleteAlert(alertId) {
  return request(`/alerts/${encodeURIComponent(alertId)}`, {
    method: 'DELETE',
  });
}

// --------------- Health ---------------

export function getHealth() {
  return request('/health');
}

// --------------- Ingest ---------------

export function getIngestStatus() {
  return request('/ingest/status');
}

export function runIngest(days = 30, maxPerPortal = 500) {
  return request(`/ingest/run?days=${days}&max_per_portal=${maxPerPortal}`, {
    method: 'POST',
  });
}
