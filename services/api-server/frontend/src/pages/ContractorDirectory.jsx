import React, { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getContractors } from '../api/client';
import { TRADES, US_STATES } from '../components/FilterPanel';

const PAGE_SIZE = 20;

export default function ContractorDirectory() {
  const navigate = useNavigate();
  const [contractors, setContractors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    trade: '',
    state: '',
  });

  const fetchContractors = useCallback(async (currentPage, currentFilters) => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        limit: PAGE_SIZE,
        offset: currentPage * PAGE_SIZE,
      };
      if (currentFilters.trade) params.trade = currentFilters.trade;
      if (currentFilters.state) params.state = currentFilters.state;

      const data = await getContractors(params);
      setContractors(data);
      setHasMore(data.length === PAGE_SIZE);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContractors(page, filters);
  }, [page, filters, fetchContractors]);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  };

  // Filter by search query (client-side for name search)
  const displayedContractors = searchQuery
    ? contractors.filter((c) =>
        (c.name || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : contractors;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Contractor Directory</h2>
          <p className="text-sm text-gray-500 mt-0.5">Browse licensed contractors and their permit history</p>
        </div>
      </div>

      {/* Filters bar */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
            <input
              type="text"
              placeholder="Search by contractor name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field pl-9"
            />
          </div>

          {/* Trade filter */}
          <select
            value={filters.trade}
            onChange={(e) => handleFilterChange('trade', e.target.value)}
            className="select-field sm:w-44"
          >
            {TRADES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>

          {/* State filter */}
          <select
            value={filters.state}
            onChange={(e) => handleFilterChange('state', e.target.value)}
            className="select-field sm:w-44"
          >
            {US_STATES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>

          {/* Reset */}
          {(filters.trade || filters.state || searchQuery) && (
            <button
              onClick={() => {
                setFilters({ trade: '', state: '' });
                setSearchQuery('');
                setPage(0);
              }}
              className="btn-secondary flex-shrink-0"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Contractor grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 rounded-lg" />
                <div>
                  <div className="h-4 w-32 bg-gray-200 rounded" />
                  <div className="h-3 w-24 bg-gray-200 rounded mt-2" />
                </div>
              </div>
              <div className="mt-4 space-y-2">
                <div className="h-3 w-full bg-gray-200 rounded" />
                <div className="h-3 w-3/4 bg-gray-200 rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : displayedContractors.length === 0 ? (
        <div className="card p-12 text-center">
          <svg className="mx-auto w-12 h-12 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
          </svg>
          <h3 className="mt-3 text-sm font-semibold text-gray-900">No contractors found</h3>
          <p className="mt-1 text-sm text-gray-500">Try adjusting your filters or search criteria.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayedContractors.map((contractor) => (
            <ContractorCard key={contractor.id} contractor={contractor} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && displayedContractors.length > 0 && (
        <div className="flex items-center justify-between">
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
          <span className="text-sm text-gray-500">Page {page + 1}</span>
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
  );
}

function ContractorCard({ contractor }) {
  const trades = contractor.trades || [];
  const licenses = contractor.licenses || [];
  const activeLicenses = licenses.filter(
    (l) => (l.status || '').toLowerCase() === 'active'
  );
  const permitCount = contractor.permit_count || contractor.recent_leads?.length || 0;

  // Generate initials from name
  const initials = (contractor.name || 'NA')
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();

  // Avatar colors — navy palette only, no rainbow
  const avatarColors = [
    'bg-primary-50 text-primary-700',
    'bg-primary-100 text-primary-800',
    'bg-gray-100 text-gray-700',
    'bg-gray-200 text-gray-800',
    'bg-primary-200 text-primary-900',
    'bg-gray-50 text-primary-700',
  ];
  const colorIndex = (contractor.name || '').charCodeAt(0) % avatarColors.length;

  return (
    <Link
      to={`/contractors/${contractor.id}`}
      className="card p-5 hover:shadow-md hover:ring-primary-200 transition-all duration-200 group block"
    >
      <div className="flex items-start gap-3">
        <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${avatarColors[colorIndex]} text-sm font-bold flex-shrink-0`}>
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 group-hover:text-primary-700 truncate transition-colors">
            {contractor.name || 'Unknown Contractor'}
          </h3>
          {contractor.addr && (
            <p className="text-xs text-gray-500 truncate mt-0.5">{contractor.addr}</p>
          )}
        </div>
      </div>

      {/* Trades */}
      {trades.length > 0 && (
        <div className="mt-3 flex items-center gap-1.5 flex-wrap">
          {trades.slice(0, 3).map((trade) => (
            <span
              key={trade}
              className="inline-flex items-center rounded-md bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600"
            >
              {trade}
            </span>
          ))}
          {trades.length > 3 && (
            <span className="text-[10px] text-gray-400">+{trades.length - 3} more</span>
          )}
        </div>
      )}

      {/* Stats row */}
      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1 text-gray-500">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
          <span>
            {activeLicenses.length} license{activeLicenses.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="flex items-center gap-1 text-gray-500">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          <span>{permitCount} permit{permitCount !== 1 ? 's' : ''}</span>
        </div>
        <span className="text-primary-600 font-medium group-hover:text-primary-700">View Profile</span>
      </div>
    </Link>
  );
}
