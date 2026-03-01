import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getLead, getLeads } from '../api/client';
import MapView from '../components/MapView';
import LeadCard from '../components/LeadCard';

function formatCurrency(value) {
  if (!value && value !== 0) return '--';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr) {
  if (!dateStr) return '--';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

function getScoreColor(score) {
  if (score >= 80) return 'bg-emerald-500';
  if (score >= 60) return 'bg-blue-500';
  if (score >= 40) return 'bg-amber-500';
  return 'bg-gray-400';
}

function getScoreLabel(score) {
  if (score >= 80) return 'Hot Lead';
  if (score >= 60) return 'Warm Lead';
  if (score >= 40) return 'Moderate';
  return 'Low Priority';
}

export default function LeadDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [lead, setLead] = useState(null);
  const [similarLeads, setSimilarLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const leadData = await getLead(id);
        if (leadData.error) {
          setError(leadData.error);
          return;
        }
        setLead(leadData);

        // Fetch similar leads (same trade)
        if (leadData.trade) {
          try {
            const similar = await getLeads({ trade: leadData.trade, limit: 4 });
            setSimilarLeads(similar.filter((l) => l.id !== id).slice(0, 3));
          } catch {
            // Not critical if similar leads fail
          }
        }
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
        <div className="h-8 w-48 bg-gray-200 rounded" />
        <div className="card p-6 space-y-4">
          <div className="h-6 w-64 bg-gray-200 rounded" />
          <div className="h-4 w-96 bg-gray-200 rounded" />
          <div className="h-4 w-80 bg-gray-200 rounded" />
        </div>
        <div className="h-80 bg-gray-200 rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <svg className="mx-auto w-12 h-12 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
        </svg>
        <h3 className="mt-3 text-lg font-semibold text-gray-900">{error === 'Lead not found' ? 'Lead Not Found' : 'Error Loading Lead'}</h3>
        <p className="mt-1 text-sm text-gray-500">{error}</p>
        <div className="mt-4 flex items-center justify-center gap-3">
          <button onClick={() => navigate(-1)} className="btn-secondary">Go Back</button>
          <Link to="/leads" className="btn-primary">Browse Leads</Link>
        </div>
      </div>
    );
  }

  if (!lead) return null;

  const score = lead.score || 0;
  const gc = lead.gc || {};
  const owner = lead.owner || {};

  // Prepare map markers
  const mapMarkers = [];
  if (lead.lat && lead.lng) {
    mapMarkers.push({
      lat: lead.lat,
      lng: lead.lng,
      label: lead.title || lead.desc?.slice(0, 60) || 'Lead Location',
      sublabel: lead.addr,
      value: formatCurrency(lead.value),
    });
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm">
        <Link to="/leads" className="text-gray-500 hover:text-gray-700">Leads</Link>
        <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
        <span className="text-gray-900 font-medium truncate max-w-xs">
          {lead.title || lead.desc?.slice(0, 40) || lead.id}
        </span>
      </nav>

      {/* Header */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-gray-900">
              {lead.title || lead.desc?.slice(0, 100) || 'Untitled Lead'}
            </h1>
            <div className="mt-2 flex items-center gap-3 flex-wrap">
              {lead.trade && (
                <span className="inline-flex items-center rounded-md bg-primary-50 px-2.5 py-1 text-xs font-semibold text-primary-700 ring-1 ring-inset ring-primary-600/20">
                  {lead.trade}
                </span>
              )}
              {lead.type && (
                <span className="inline-flex items-center rounded-md bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10 capitalize">
                  {lead.type}
                </span>
              )}
              {lead.status && (
                <span className="inline-flex items-center rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20 capitalize">
                  {lead.status}
                </span>
              )}
            </div>
          </div>
          {/* Score */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="text-right">
              <p className="text-xs text-gray-500 font-medium">{getScoreLabel(score)}</p>
            </div>
            <div className={`flex items-center justify-center w-16 h-16 rounded-2xl ${getScoreColor(score)} text-white font-bold text-2xl shadow-lg`}>
              {score}
            </div>
          </div>
        </div>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Key info */}
          <div className="card p-6">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Project Details</h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
              <div>
                <dt className="text-xs font-medium text-gray-500">Estimated Value</dt>
                <dd className="mt-1 text-lg font-bold text-gray-900">{formatCurrency(lead.value)}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium text-gray-500">Posted Date</dt>
                <dd className="mt-1 text-sm text-gray-900">{formatDate(lead.posted)}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-xs font-medium text-gray-500">Address</dt>
                <dd className="mt-1 text-sm text-gray-900">{lead.addr || '--'}</dd>
              </div>
              {lead.desc && (
                <div className="sm:col-span-2">
                  <dt className="text-xs font-medium text-gray-500">Description</dt>
                  <dd className="mt-1 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{lead.desc}</dd>
                </div>
              )}
              {lead.permit_no && (
                <div>
                  <dt className="text-xs font-medium text-gray-500">Permit Number</dt>
                  <dd className="mt-1 text-sm text-gray-900 font-mono">{lead.permit_no}</dd>
                </div>
              )}
              {lead.source && (
                <div>
                  <dt className="text-xs font-medium text-gray-500">Source</dt>
                  <dd className="mt-1 text-sm text-gray-900">{lead.source}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Map */}
          {mapMarkers.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-900 mb-3">Location</h2>
              <MapView
                markers={mapMarkers}
                center={[mapMarkers[0].lat, mapMarkers[0].lng]}
                zoom={14}
                height="350px"
              />
            </div>
          )}

          {/* Similar leads */}
          {similarLeads.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-900">Similar Leads</h2>
                <Link to={`/leads?trade=${lead.trade}`} className="text-xs font-medium text-primary-600 hover:text-primary-700">
                  View more
                </Link>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {similarLeads.map((sl) => (
                  <LeadCard key={sl.id} lead={sl} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right sidebar */}
        <div className="space-y-6">
          {/* Contractor / GC */}
          <div className="card p-6">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
                </svg>
                General Contractor
              </div>
            </h2>
            {gc.n ? (
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{gc.n}</p>
                  {gc.phone && (
                    <a href={`tel:${gc.phone}`} className="block text-sm text-primary-600 hover:text-primary-700 mt-1">
                      {gc.phone}
                    </a>
                  )}
                  {gc.email && (
                    <a href={`mailto:${gc.email}`} className="block text-sm text-primary-600 hover:text-primary-700 mt-0.5">
                      {gc.email}
                    </a>
                  )}
                  {gc.lic && (
                    <p className="text-xs text-gray-500 mt-1">License: {gc.lic}</p>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-400">No contractor information available</p>
            )}
          </div>

          {/* Owner */}
          <div className="card p-6">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
                Property Owner
              </div>
            </h2>
            {owner.n || owner.name ? (
              <div className="space-y-2">
                <p className="text-sm font-semibold text-gray-900">{owner.n || owner.name}</p>
                {(owner.phone) && (
                  <a href={`tel:${owner.phone}`} className="block text-sm text-primary-600 hover:text-primary-700">
                    {owner.phone}
                  </a>
                )}
                {(owner.email) && (
                  <a href={`mailto:${owner.email}`} className="block text-sm text-primary-600 hover:text-primary-700">
                    {owner.email}
                  </a>
                )}
                {(owner.addr) && (
                  <p className="text-xs text-gray-500">{owner.addr}</p>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No owner information available</p>
            )}
          </div>

          {/* Score breakdown */}
          <div className="card p-6">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">Score Breakdown</h2>
            <div className="space-y-3">
              {[
                { label: 'Data Quality', value: lead.score_data || Math.min(score, 30), max: 30 },
                { label: 'Recency', value: lead.score_recency || Math.min(Math.max(score - 20, 0), 25), max: 25 },
                { label: 'Value Signal', value: lead.score_value || Math.min(Math.max(score - 30, 0), 25), max: 25 },
                { label: 'Market Fit', value: lead.score_market || Math.max(score - 60, 0), max: 20 },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-600">{item.label}</span>
                    <span className="font-semibold text-gray-900">{item.value}/{item.max}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full transition-all duration-500"
                      style={{ width: `${(item.value / item.max) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="card p-6 space-y-3">
            <h2 className="text-sm font-semibold text-gray-900 mb-2">Actions</h2>
            <button className="btn-primary w-full justify-center">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
              Set Alert for Similar
            </button>
            <button className="btn-secondary w-full justify-center">
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
              </svg>
              Share Lead
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
