import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getContractor } from '../api/client';
import LeadCard from '../components/LeadCard';
import ChartWidget from '../components/ChartWidget';

function formatDate(dateStr) {
  if (!dateStr) return '--';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export default function ContractorProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [contractor, setContractor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const data = await getContractor(id);
        if (data.error) {
          setError(data.error);
          return;
        }
        setContractor(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="card p-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gray-200 rounded-xl" />
            <div>
              <div className="h-6 w-48 bg-gray-200 rounded" />
              <div className="h-4 w-32 bg-gray-200 rounded mt-2" />
            </div>
          </div>
        </div>
        <div className="card p-6 h-64 bg-gray-100 rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto w-12 h-12 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
        </svg>
        <h3 className="mt-3 text-lg font-semibold text-gray-900">
          {error === 'Contractor not found' ? 'Contractor Not Found' : 'Error Loading Profile'}
        </h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <div className="mt-4 flex items-center justify-center gap-3">
          <button onClick={() => navigate(-1)} className="btn-secondary">Go Back</button>
          <Link to="/contractors" className="btn-primary">Browse Contractors</Link>
        </div>
      </div>
    );
  }

  if (!contractor) return null;

  const trades = contractor.trades || [];
  const licenses = contractor.licenses || [];
  const recentLeads = contractor.recent_leads || [];

  // Generate avatar
  const initials = (contractor.name || 'NA')
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();

  // Compute stats from licenses/leads
  const activeLicenses = licenses.filter((l) => (l.status || '').toLowerCase() === 'active');
  const expiredLicenses = licenses.filter((l) => (l.status || '').toLowerCase() === 'expired');

  // Trade distribution from permits
  const tradeDistribution = {};
  recentLeads.forEach((lead) => {
    const trade = lead.trade || 'Other';
    tradeDistribution[trade] = (tradeDistribution[trade] || 0) + 1;
  });
  const tradeChartData = Object.entries(tradeDistribution).map(([name, value]) => ({
    name: name.charAt(0) + name.slice(1).toLowerCase(),
    value,
  }));

  // Value distribution from permits
  const valueData = recentLeads
    .filter((l) => l.value)
    .map((l) => ({
      name: (l.title || l.desc || '').slice(0, 15),
      value: l.value,
    }))
    .slice(0, 10);

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'licenses', label: `Licenses (${licenses.length})` },
    { key: 'permits', label: `Permits (${recentLeads.length})` },
  ];

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm">
        <Link to="/contractors" className="text-gray-500 hover:text-gray-700">Contractors</Link>
        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
        <span className="text-gray-900 font-medium truncate">{contractor.name || contractor.id}</span>
      </nav>

      {/* Profile header */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row sm:items-start gap-4">
          <div className="flex items-center justify-center w-16 h-16 rounded-xl bg-primary-100 text-primary-700 text-xl font-bold flex-shrink-0">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-gray-900">{contractor.name || 'Unknown Contractor'}</h1>
            {contractor.addr && (
              <p className="text-sm text-gray-500 mt-1 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                </svg>
                {contractor.addr}
              </p>
            )}
            {trades.length > 0 && (
              <div className="mt-3 flex items-center gap-2 flex-wrap">
                {trades.map((trade) => (
                  <span
                    key={trade}
                    className="inline-flex items-center rounded-md bg-primary-50 px-2 py-0.5 text-xs font-semibold text-primary-700 ring-1 ring-inset ring-primary-600/20"
                  >
                    {trade}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="flex sm:flex-col items-center sm:items-end gap-4 sm:gap-2">
            {contractor.phone && (
              <a href={`tel:${contractor.phone}`} className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
                </svg>
                {contractor.phone}
              </a>
            )}
            {contractor.email && (
              <a href={`mailto:${contractor.email}`} className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                </svg>
                {contractor.email}
              </a>
            )}
          </div>
        </div>

        {/* Stats bar */}
        <div className="mt-6 pt-4 border-t border-gray-100 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{licenses.length}</p>
            <p className="text-xs text-gray-500 mt-0.5">Total Licenses</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-emerald-600">{activeLicenses.length}</p>
            <p className="text-xs text-gray-500 mt-0.5">Active Licenses</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{recentLeads.length}</p>
            <p className="text-xs text-gray-500 mt-0.5">Permits</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-900">{trades.length}</p>
            <p className="text-xs text-gray-500 mt-0.5">Trades</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Trade Distribution */}
          {tradeChartData.length > 0 && (
            <ChartWidget
              type="bar"
              title="Permit Trade Distribution"
              subtitle="Breakdown of permits by trade type"
              data={tradeChartData}
              height={250}
            />
          )}

          {/* Value Distribution */}
          {valueData.length > 0 && (
            <ChartWidget
              type="bar"
              title="Recent Project Values"
              subtitle="Estimated values of recent permits"
              data={valueData}
              height={250}
              formatter={(v) =>
                new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 0,
                }).format(v)
              }
            />
          )}

          {/* Business info card */}
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Business Information</h3>
            <dl className="space-y-3">
              {contractor.name && (
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Business Name</dt>
                  <dd className="text-sm font-medium text-gray-900">{contractor.name}</dd>
                </div>
              )}
              {contractor.addr && (
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Address</dt>
                  <dd className="text-sm font-medium text-gray-900 text-right max-w-[200px]">{contractor.addr}</dd>
                </div>
              )}
              {contractor.ein && (
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">EIN</dt>
                  <dd className="text-sm font-mono text-gray-900">{contractor.ein}</dd>
                </div>
              )}
              {contractor.entity_type && (
                <div className="flex justify-between">
                  <dt className="text-sm text-gray-500">Entity Type</dt>
                  <dd className="text-sm font-medium text-gray-900">{contractor.entity_type}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Quick license summary */}
          <div className="card p-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">License Summary</h3>
            {licenses.length > 0 ? (
              <div className="space-y-3">
                {licenses.slice(0, 5).map((lic, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{lic.type || lic.trade || 'License'}</p>
                      <p className="text-xs text-gray-500">
                        {lic.state || '--'} {lic.number ? `#${lic.number}` : ''}
                      </p>
                    </div>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      (lic.status || '').toLowerCase() === 'active'
                        ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20'
                        : 'bg-gray-100 text-gray-600 ring-1 ring-gray-500/20'
                    }`}>
                      {lic.status || 'Unknown'}
                    </span>
                  </div>
                ))}
                {licenses.length > 5 && (
                  <button
                    onClick={() => setActiveTab('licenses')}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                  >
                    View all {licenses.length} licenses
                  </button>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No license records found</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'licenses' && (
        <div className="card overflow-hidden">
          {licenses.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Number</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">State</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Issued</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Expires</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {licenses.map((lic, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {lic.type || lic.trade || '--'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 font-mono">
                        {lic.number || '--'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {lic.state || '--'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
                          (lic.status || '').toLowerCase() === 'active'
                            ? 'bg-emerald-50 text-emerald-700 ring-emerald-600/20'
                            : (lic.status || '').toLowerCase() === 'expired'
                              ? 'bg-red-50 text-red-700 ring-red-600/20'
                              : 'bg-gray-100 text-gray-600 ring-gray-500/20'
                        }`}>
                          {lic.status || 'Unknown'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {formatDate(lic.issued || lic.issue_date)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">
                        {formatDate(lic.expires || lic.exp_date)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center text-sm text-gray-400">
              No license records found
            </div>
          )}
        </div>
      )}

      {activeTab === 'permits' && (
        <div>
          {recentLeads.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentLeads.map((lead) => (
                <LeadCard key={lead.id} lead={lead} />
              ))}
            </div>
          ) : (
            <div className="card p-12 text-center text-sm text-gray-400">
              No permit history found
            </div>
          )}
        </div>
      )}
    </div>
  );
}
