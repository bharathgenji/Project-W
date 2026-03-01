import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getDashboard, getLeads } from '../api/client';
import StatsCard from '../components/StatsCard';
import ChartWidget from '../components/ChartWidget';
import LeadCard from '../components/LeadCard';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentLeads, setRecentLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [dashData, leadsData] = await Promise.all([
          getDashboard(),
          getLeads({ sort_by: 'date', limit: 6 }),
        ]);
        setStats(dashData);
        setRecentLeads(leadsData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-xl bg-red-50 p-6 text-center">
        <svg className="mx-auto w-10 h-10 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
        <h3 className="mt-2 text-sm font-semibold text-red-800">Failed to load dashboard</h3>
        <p className="mt-1 text-sm text-red-600">{error}</p>
        <button onClick={() => window.location.reload()} className="mt-3 btn-primary">
          Retry
        </button>
      </div>
    );
  }

  // Prepare trade chart data
  const tradeChartData = stats?.by_trade
    ? Object.entries(stats.by_trade).map(([name, value]) => ({
        name: name.charAt(0) + name.slice(1).toLowerCase(),
        value,
      }))
    : [];

  // Prepare value distribution data
  const valueChartData = stats?.by_value_range
    ? [
        { name: 'Under $50k', value: stats.by_value_range.under_50k || 0 },
        { name: '$50k-$200k', value: stats.by_value_range['50k_200k'] || 0 },
        { name: 'Over $200k', value: stats.by_value_range.over_200k || 0 },
      ]
    : [];

  // Prepare type distribution
  const typeChartData = stats?.by_type
    ? Object.entries(stats.by_type).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Leads"
          value={stats?.total_leads?.toLocaleString() || '0'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          }
          color="primary"
        />
        <StatsCard
          title="New This Week"
          value={stats?.new_this_week?.toLocaleString() || '0'}
          change={stats?.new_this_week && stats?.total_leads ? Math.round((stats.new_this_week / stats.total_leads) * 100) : null}
          changeLabel="of total"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="green"
        />
        <StatsCard
          title="New Today"
          value={stats?.new_today?.toLocaleString() || '0'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
          }
          color="amber"
        />
        <StatsCard
          title="Total Contractors"
          value={stats?.total_contractors?.toLocaleString() || '0'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
            </svg>
          }
          color="blue"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartWidget
          type="bar"
          title="Leads by Trade"
          subtitle="Distribution across construction trades"
          data={tradeChartData}
          height={280}
        />
        <ChartWidget
          type="bar"
          title="Project Value Distribution"
          subtitle="Leads grouped by estimated project value"
          data={valueChartData}
          height={280}
          colors={['#0891b2', '#4f46e5', '#059669']}
        />
      </div>

      {/* Hot markets + Lead type */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Hot Markets */}
        <div className="card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-900">Hot Markets</h3>
              <p className="text-xs text-gray-500 mt-0.5">Cities with the most construction activity</p>
            </div>
            <Link to="/markets" className="text-xs font-medium text-primary-600 hover:text-primary-700">
              View all
            </Link>
          </div>
          {stats?.hot_markets?.length > 0 ? (
            <div className="space-y-3">
              {stats.hot_markets.slice(0, 8).map((market, index) => {
                const maxCount = stats.hot_markets[0].count;
                const percentage = maxCount > 0 ? (market.count / maxCount) * 100 : 0;
                return (
                  <div key={market.city} className="flex items-center gap-3">
                    <span className="text-xs font-medium text-gray-400 w-5 text-right">{index + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-900 truncate">{market.city}</span>
                        <span className="text-sm font-semibold text-gray-700 ml-2">{market.count}</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-500 rounded-full transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-400 py-8 text-center">No market data available</p>
          )}
        </div>

        {/* Lead type breakdown */}
        <ChartWidget
          type="bar"
          title="Lead Types"
          subtitle="Permits vs Bids"
          data={typeChartData}
          height={250}
          colors={['#4f46e5', '#0891b2']}
        />
      </div>

      {/* Recent leads */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Recent Leads</h3>
            <p className="text-sm text-gray-500 mt-0.5">Latest construction opportunities</p>
          </div>
          <Link to="/leads" className="btn-secondary text-sm">
            View All Leads
          </Link>
        </div>
        {recentLeads.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentLeads.map((lead) => (
              <LeadCard key={lead.id} lead={lead} />
            ))}
          </div>
        ) : (
          <div className="card p-8 text-center text-sm text-gray-400">
            No recent leads available
          </div>
        )}
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card p-6">
            <div className="h-4 w-24 bg-gray-200 rounded" />
            <div className="mt-3 h-8 w-16 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6 h-80 bg-gray-100 rounded-xl" />
        <div className="card p-6 h-80 bg-gray-100 rounded-xl" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="card p-5 h-40 bg-gray-100 rounded-xl" />
        ))}
      </div>
    </div>
  );
}
