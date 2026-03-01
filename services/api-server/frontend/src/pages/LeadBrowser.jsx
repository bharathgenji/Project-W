import React, { useEffect, useState, useCallback } from 'react';
import { getLeads } from '../api/client';
import FilterPanel from '../components/FilterPanel';
import LeadTable from '../components/LeadTable';

const PAGE_SIZE = 20;

export default function LeadBrowser() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [totalEstimate, setTotalEstimate] = useState(null);
  const [filters, setFilters] = useState({
    trade: '',
    state: '',
    min_value: '',
    max_value: '',
    sort_by: 'score',
  });
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

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

      const data = await getLeads(params);
      setLeads(data);
      setHasMore(data.length === PAGE_SIZE);
      if (currentPage === 0 && data.length < PAGE_SIZE) {
        setTotalEstimate(data.length);
      } else {
        setTotalEstimate(null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLeads(page, filters);
  }, [page, filters, fetchLeads]);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
    setPage(0);
  };

  const handleReset = () => {
    setFilters({
      trade: '',
      state: '',
      min_value: '',
      max_value: '',
      sort_by: 'score',
    });
    setPage(0);
  };

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
            <FilterPanel
              filters={filters}
              onChange={(f) => { handleFilterChange(f); setMobileFiltersOpen(false); }}
              onReset={() => { handleReset(); setMobileFiltersOpen(false); }}
            />
          </div>
        </div>
      )}

      {/* Desktop sidebar filters */}
      <div className="hidden lg:block w-64 flex-shrink-0">
        <div className="sticky top-24">
          <FilterPanel
            filters={filters}
            onChange={handleFilterChange}
            onReset={handleReset}
          />
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Construction Leads</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              {loading
                ? 'Loading...'
                : totalEstimate !== null
                  ? `${totalEstimate} leads found`
                  : `Showing ${page * PAGE_SIZE + 1} - ${page * PAGE_SIZE + leads.length}`
              }
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 hidden sm:inline">Page {page + 1}</span>
          </div>
        </div>

        {/* Error state */}
        {error && (
          <div className="rounded-lg bg-red-50 p-4 mb-4">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Lead table */}
        <LeadTable leads={leads} loading={loading} />

        {/* Pagination */}
        {!loading && leads.length > 0 && (
          <div className="mt-4 flex items-center justify-between">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4 mr-1.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
              </svg>
              Previous
            </button>
            <div className="flex items-center gap-1">
              {page > 1 && (
                <button onClick={() => setPage(0)} className="w-8 h-8 rounded-lg text-sm text-gray-600 hover:bg-gray-100">
                  1
                </button>
              )}
              {page > 2 && <span className="text-gray-400 px-1">...</span>}
              {page > 0 && (
                <button onClick={() => setPage(page - 1)} className="w-8 h-8 rounded-lg text-sm text-gray-600 hover:bg-gray-100">
                  {page}
                </button>
              )}
              <button className="w-8 h-8 rounded-lg text-sm font-semibold bg-primary-600 text-white">
                {page + 1}
              </button>
              {hasMore && (
                <button onClick={() => setPage(page + 1)} className="w-8 h-8 rounded-lg text-sm text-gray-600 hover:bg-gray-100">
                  {page + 2}
                </button>
              )}
            </div>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasMore}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
              <svg className="w-4 h-4 ml-1.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
