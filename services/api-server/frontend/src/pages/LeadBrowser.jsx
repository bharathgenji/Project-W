import React, { useEffect, useState, useCallback } from 'react';
import { getLeads } from '../api/client';
import FilterPanel from '../components/FilterPanel';
import LeadCard from '../components/LeadCard';
import LeadTable from '../components/LeadTable';

const PAGE_SIZE = 20;

export default function LeadBrowser() {
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [viewMode, setViewMode] = useState(() =>
    window.innerWidth < 768 ? 'cards' : 'table'
  );
  const [filters, setFilters] = useState({
    trade: '', state: '', min_value: '', max_value: '', sort_by: 'score',
  });

  const fetchLeads = useCallback(async (currentPage, currentFilters) => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        limit: PAGE_SIZE,
        offset: currentPage * PAGE_SIZE,
        sort_by: currentFilters.sort_by || 'score',
      };
      if (currentFilters.trade) params.trade = currentFilters.trade;
      if (currentFilters.state) params.state = currentFilters.state;
      if (currentFilters.min_value) params.min_value = Number(currentFilters.min_value);
      if (currentFilters.max_value) params.max_value = Number(currentFilters.max_value);

      // API now returns { data, total, offset, limit, has_more }
      const envelope = await getLeads(params);
      const data = Array.isArray(envelope) ? envelope : (envelope.data || []);
      const tot = typeof envelope.total === 'number' ? envelope.total : null;

      setLeads(data);
      setTotal(tot);
      setHasMore(envelope.has_more ?? data.length === PAGE_SIZE);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchLeads(page, filters); }, [page, filters, fetchLeads]);

  const handleFilterChange = (newFilters) => { setFilters(newFilters); setPage(0); };
  const handleReset = () => { setFilters({ trade: '', state: '', min_value: '', max_value: '', sort_by: 'score' }); setPage(0); };

  // Build export URL from current filters
  const exportUrl = (() => {
    const p = new URLSearchParams();
    if (filters.trade) p.set('trade', filters.trade);
    if (filters.state) p.set('state', filters.state);
    if (filters.min_value) p.set('min_value', filters.min_value);
    if (filters.max_value) p.set('max_value', filters.max_value);
    return `/api/leads/export?${p.toString()}`;
  })();

  const start = page * PAGE_SIZE + 1;
  const end = page * PAGE_SIZE + leads.length;
  const countText = loading
    ? 'Loading...'
    : total !== null
      ? `${start}–${end} of ${total.toLocaleString()} leads`
      : leads.length > 0
        ? `Showing ${start}–${end}`
        : 'No leads found';

  return (
    <div className="flex gap-6 relative">
      {/* Mobile filter toggle */}
      <div className="lg:hidden fixed bottom-6 right-6 z-20">
        <button
          onClick={() => setMobileFiltersOpen(!mobileFiltersOpen)}
          className="btn-primary shadow-lg rounded-full w-14 h-14 flex items-center justify-center"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
          </svg>
        </button>
      </div>

      {/* Mobile filter overlay */}
      {mobileFiltersOpen && (
        <div className="fixed inset-0 z-30 lg:hidden">
          <div className="fixed inset-0 bg-gray-600/75" onClick={() => setMobileFiltersOpen(false)} />
          <div className="fixed inset-y-0 left-0 w-80 bg-white overflow-y-auto p-4 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
              <button onClick={() => setMobileFiltersOpen(false)} className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <FilterPanel filters={filters} onChange={(f) => { handleFilterChange(f); setMobileFiltersOpen(false); }} onReset={() => { handleReset(); setMobileFiltersOpen(false); }} />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:block w-64 flex-shrink-0">
        <div className="sticky top-24">
          <FilterPanel filters={filters} onChange={handleFilterChange} onReset={handleReset} />
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Header bar */}
        <div className="flex items-center justify-between mb-4 gap-2 flex-wrap">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Construction Leads</h2>
            <p className="text-sm text-gray-500 mt-0.5">{countText}</p>
          </div>

          <div className="flex items-center gap-2">
            {/* View toggle */}
            <div className="flex rounded-lg border border-gray-200 overflow-hidden">
              <button
                onClick={() => setViewMode('table')}
                title="Table view"
                className={`px-2.5 py-1.5 text-xs ${viewMode === 'table' ? 'bg-primary-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'}`}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 1.5v-1.5m0 0c0-.621.504-1.125 1.125-1.125m0 0h7.5" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('cards')}
                title="Card view"
                className={`px-2.5 py-1.5 text-xs ${viewMode === 'cards' ? 'bg-primary-600 text-white' : 'bg-white text-gray-500 hover:bg-gray-50'}`}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                </svg>
              </button>
            </div>

            {/* CSV Export */}
            <a
              href={exportUrl}
              download
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Export CSV
            </a>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Cards view (mobile-first) */}
        {viewMode === 'cards' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {loading
              ? Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="card p-5 animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-3" />
                    <div className="h-3 bg-gray-100 rounded w-1/2 mb-2" />
                    <div className="h-3 bg-gray-100 rounded w-2/3" />
                  </div>
                ))
              : leads.map((lead) => <LeadCard key={lead.id} lead={lead} />)
            }
          </div>
        )}

        {/* Table view */}
        {viewMode === 'table' && <LeadTable leads={leads} loading={loading} />}

        {/* Pagination */}
        {!loading && leads.length > 0 && (
          <div className="mt-6 flex items-center justify-between">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="btn-secondary disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
              Prev
            </button>

            <span className="text-sm text-gray-500">{countText}</span>

            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasMore}
              className="btn-secondary disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
            >
              Next
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </button>
          </div>
        )}

        {!loading && leads.length === 0 && !error && (
          <div className="text-center py-16 text-gray-400">
            <div className="text-4xl mb-3">🔍</div>
            <p className="font-medium text-gray-600">No leads match your filters</p>
            <button onClick={handleReset} className="mt-3 text-sm text-primary-600 hover:underline">Clear filters</button>
          </div>
        )}
      </div>
    </div>
  );
}
