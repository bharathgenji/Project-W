import React, { useEffect, useState, useCallback } from 'react';
import { createAlert, getAlerts, deleteAlert } from '../api/client';
import { TRADES, US_STATES } from '../components/FilterPanel';

function formatDate(dateStr) {
  if (!dateStr) return '--';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return dateStr;
  }
}

const EMPTY_FORM = {
  email: '',
  trade: '',
  state: '',
  city: '',
  min_value: '',
  max_value: '',
};

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [emailFilter, setEmailFilter] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState(null);
  const [createSuccess, setCreateSuccess] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAlerts(emailFilter || undefined);
      setAlerts(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [emailFilter]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleFormChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setCreateError(null);
    setCreateSuccess(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCreateError(null);
    setCreateSuccess(false);

    if (!form.email || !form.email.includes('@')) {
      setCreateError('Please enter a valid email address.');
      return;
    }

    if (!form.trade && !form.state && !form.min_value) {
      setCreateError('Please set at least one filter criterion (trade, state, or minimum value).');
      return;
    }

    setCreating(true);
    try {
      const alertData = {
        email: form.email.trim(),
        trade: form.trade || null,
        state: form.state || null,
        city: form.city.trim() || null,
        min_value: form.min_value ? Number(form.min_value) : null,
        max_value: form.max_value ? Number(form.max_value) : null,
      };
      await createAlert(alertData);
      setCreateSuccess(true);
      setForm({ ...EMPTY_FORM, email: form.email }); // Keep the email for convenience
      fetchAlerts();
    } catch (err) {
      setCreateError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (alertId) => {
    if (!window.confirm('Are you sure you want to delete this alert?')) return;

    setDeletingId(alertId);
    try {
      await deleteAlert(alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch (err) {
      setError(`Failed to delete alert: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Lead Alerts</h2>
        <p className="text-sm text-gray-500 mt-0.5">
          Set up email notifications for new construction leads matching your criteria.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Create alert form */}
        <div className="lg:col-span-2">
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-1">Create New Alert</h3>
            <p className="text-xs text-gray-500 mb-5">Get notified when new leads match your criteria.</p>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1.5">
                  Email Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => handleFormChange('email', e.target.value)}
                  placeholder="your@email.com"
                  required
                  className="input-field"
                />
              </div>

              {/* Trade */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1.5">Trade</label>
                <select
                  value={form.trade}
                  onChange={(e) => handleFormChange('trade', e.target.value)}
                  className="select-field"
                >
                  {TRADES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              {/* State */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1.5">State</label>
                <select
                  value={form.state}
                  onChange={(e) => handleFormChange('state', e.target.value)}
                  className="select-field"
                >
                  {US_STATES.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>

              {/* City */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1.5">City (optional)</label>
                <input
                  type="text"
                  value={form.city}
                  onChange={(e) => handleFormChange('city', e.target.value)}
                  placeholder="e.g., Los Angeles"
                  className="input-field"
                />
              </div>

              {/* Value range */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1.5">Value Range</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    placeholder="Min ($)"
                    value={form.min_value}
                    onChange={(e) => handleFormChange('min_value', e.target.value)}
                    className="input-field"
                  />
                  <span className="text-gray-400 text-sm flex-shrink-0">to</span>
                  <input
                    type="number"
                    placeholder="Max ($)"
                    value={form.max_value}
                    onChange={(e) => handleFormChange('max_value', e.target.value)}
                    className="input-field"
                  />
                </div>
              </div>

              {/* Error */}
              {createError && (
                <div className="rounded-lg bg-red-50 p-3">
                  <p className="text-sm text-red-700">{createError}</p>
                </div>
              )}

              {/* Success */}
              {createSuccess && (
                <div className="rounded-lg bg-emerald-50 p-3">
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                    <p className="text-sm text-emerald-700">Alert created successfully!</p>
                  </div>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={creating}
                className="btn-primary w-full justify-center disabled:opacity-50"
              >
                {creating ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Creating...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                    </svg>
                    Create Alert
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Existing alerts */}
        <div className="lg:col-span-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900">Your Alerts</h3>
            <div className="flex items-center gap-2">
              <input
                type="email"
                placeholder="Filter by email..."
                value={emailFilter}
                onChange={(e) => setEmailFilter(e.target.value)}
                className="input-field w-48 text-xs"
              />
              <button onClick={fetchAlerts} className="btn-secondary text-xs px-3 py-2">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                </svg>
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-lg bg-red-50 p-4 mb-4">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Loading */}
          {loading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="card p-5 animate-pulse">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-200 rounded-lg" />
                    <div className="flex-1">
                      <div className="h-4 w-48 bg-gray-200 rounded" />
                      <div className="h-3 w-32 bg-gray-200 rounded mt-2" />
                    </div>
                    <div className="w-16 h-8 bg-gray-200 rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : alerts.length === 0 ? (
            <div className="card p-12 text-center">
              <svg className="mx-auto w-12 h-12 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
              <h3 className="mt-3 text-sm font-semibold text-gray-900">No alerts yet</h3>
              <p className="mt-1 text-sm text-gray-500">Create your first alert using the form to start receiving notifications.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  onDelete={handleDelete}
                  deleting={deletingId === alert.id}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AlertCard({ alert, onDelete, deleting }) {
  const criteria = [];
  if (alert.trade) criteria.push({ label: 'Trade', value: alert.trade });
  if (alert.state) {
    const stateObj = US_STATES.find((s) => s.value === alert.state);
    criteria.push({ label: 'State', value: stateObj?.label || alert.state });
  }
  if (alert.city) criteria.push({ label: 'City', value: alert.city });
  if (alert.min_value) {
    criteria.push({
      label: 'Min Value',
      value: new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
      }).format(alert.min_value),
    });
  }
  if (alert.max_value) {
    criteria.push({
      label: 'Max Value',
      value: new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
      }).format(alert.max_value),
    });
  }

  return (
    <div className="card p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className={`flex items-center justify-center w-9 h-9 rounded-lg flex-shrink-0 ${
            alert.active !== false ? 'bg-primary-50 text-primary-600' : 'bg-gray-100 text-gray-400'
          }`}>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
            </svg>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-900">{alert.email}</p>
            <div className="mt-1.5 flex items-center gap-2 flex-wrap">
              {criteria.map((c) => (
                <span
                  key={c.label}
                  className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600"
                >
                  <span className="text-gray-400 mr-1">{c.label}:</span>
                  {c.value}
                </span>
              ))}
              {criteria.length === 0 && (
                <span className="text-xs text-gray-400">No specific criteria</span>
              )}
            </div>
            <p className="mt-1.5 text-xs text-gray-400">
              Created {formatDate(alert.created)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
            alert.active !== false
              ? 'bg-emerald-50 text-emerald-700'
              : 'bg-gray-100 text-gray-500'
          }`}>
            {alert.active !== false ? 'Active' : 'Paused'}
          </span>
          <button
            onClick={() => onDelete(alert.id)}
            disabled={deleting}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
            title="Delete alert"
          >
            {deleting ? (
              <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
