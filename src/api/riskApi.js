/**
 * Centralized API client for GST Risk Intelligence, Exposure Analytics, and Knowledge Graph.
 * Communicates strictly with backend endpoints using VITE_API_URL or default http://localhost:8000.
 */

const BASE_URL = (import.meta.env?.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

async function handleResponse(res) {
  if (!res.ok) {
    let errorMessage = `HTTP error ${res.status}: ${res.statusText}`;
    try {
      const errData = await res.json();
      if (errData && errData.detail) {
        errorMessage = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch (_) {
      // Keep default error message
    }
    const error = new Error(errorMessage);
    error.status = res.status;
    throw error;
  }
  return res.json();
}

/**
 * Fetch dynamic benchmark risk summary, distributions, ITC exposure, and priorities.
 */
export async function getRiskSummary(period) {
  const url = period ? `${BASE_URL}/risk/summary?period=${encodeURIComponent(period)}` : `${BASE_URL}/risk/summary`;
  const res = await fetch(url);
  return handleResponse(res);
}

/**
 * Fetch paginated, filtered, and sorted vendor risk evaluations.
 */
export async function getVendors(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') {
      query.append(k, v);
    }
  });
  const qs = query.toString();
  const url = qs ? `${BASE_URL}/risk/vendors?${qs}` : `${BASE_URL}/risk/vendors`;
  const res = await fetch(url);
  return handleResponse(res);
}

/**
 * Fetch detailed vendor risk assessment, Tree SHAP factors, and multi-domain evidence.
 */
export async function getVendor(vendorId, period) {
  const pParam = period ? `?period=${encodeURIComponent(period)}` : '';
  const url = `${BASE_URL}/risk/vendor/${encodeURIComponent(vendorId)}${pParam}`;
  const res = await fetch(url);
  return handleResponse(res);
}

/**
 * Fetch chronological risk history and transition analysis for vendor.
 */
export async function getVendorHistory(vendorId) {
  const url = `${BASE_URL}/risk/vendor/${encodeURIComponent(vendorId)}/history`;
  const res = await fetch(url);
  return handleResponse(res);
}

/**
 * Fetch time-safe interactive Knowledge Graph neighborhood (depth 1 or 2).
 */
export async function getVendorGraph(vendorId, period = '2026-02', depth = 1) {
  const url = `${BASE_URL}/risk/vendor/${encodeURIComponent(vendorId)}/graph?period=${encodeURIComponent(period)}&depth=${depth}`;
  const res = await fetch(url);
  return handleResponse(res);
}

/**
 * Request real-time risk prediction and Tree SHAP evaluation.
 */
export async function predictRisk(payload) {
  const res = await fetch(`${BASE_URL}/risk/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}
