import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getDashboard, getLeads } from '../api/client';
import ChartWidget from '../components/ChartWidget';
import LeadCard from '../components/LeadCard';

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmt(v) {
  if (!v && v !== 0) return '--';
  if (v >= 1e9) return `$${(v/1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${Math.round(v/1e3)}K`;
  return `$${v}`;
}

const TRADE_COLORS = {
  ELECTRICAL:'#f59e0b', PLUMBING:'#3b82f6', HVAC:'#06b6d4',
  ROOFING:'#f97316', Electrical:'#f59e0b', Plumbing:'#3b82f6',
  Hvac:'#06b6d4', Roofing:'#f97316', Concrete:'#6b7280',
  General:'#8b5cf6', CONCRETE:'#6b7280', GENERAL:'#8b5cf6',
};
const TRADE_EMOJI = {
  ELECTRICAL:'⚡', PLUMBING:'🔧', HVAC:'❄️', ROOFING:'🏠', CONCRETE:'🏗️', GENERAL:'🔨',
  Electrical:'⚡', Plumbing:'🔧', Hvac:'❄️', Roofing:'🏠', Concrete:'🏗️', General:'🔨',
};

// ── Skeleton ──────────────────────────────────────────────────────────────────
function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <div key={i} className="h-28 rounded-2xl bg-gray-200"/>)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-64 rounded-2xl bg-gray-200"/>
        <div className="h-64 rounded-2xl bg-gray-200"/>
      </div>
      <div className="h-48 rounded-2xl bg-gray-200"/>
    </div>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ icon, label, value, sub, gradient, trend }) {
  return (
    <div className={`rounded-2xl p-5 text-white relative overflow-hidden shadow-lg ${gradient}`}>
      <div className="absolute top-0 right-0 w-24 h-24 rounded-full bg-white/10 translate-x-6 -translate-y-6"/>
      <div className="relative">
        <div className="text-2xl mb-2">{icon}</div>
        <div className="text-3xl font-black tracking-tight">{value}</div>
        <div className="text-sm font-medium opacity-90 mt-1">{label}</div>
        {sub && <div className="text-xs opacity-70 mt-1">{sub}</div>}
        {trend && (
          <div className="mt-2 flex items-center gap-1 text-xs font-semibold bg-white/20 rounded-full px-2 py-0.5 w-fit">
            {trend}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Hot Market Badge ──────────────────────────────────────────────────────────
function HotMarketBadge({ city, count, rank }) {
  const colors = [
    'bg-amber-500', 'bg-orange-400', 'bg-blue-500',
    'bg-emerald-500', 'bg-purple-500', 'bg-rose-500',
  ];
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-gray-100 last:border-0">
      <span className={`w-6 h-6 rounded-full text-white text-xs font-bold flex items-center justify-center flex-shrink-0 ${colors[rank] || 'bg-gray-400'}`}>
        {rank + 1}
      </span>
      <span className="font-semibold text-gray-800 flex-1 truncate">{city}</span>
      <span className="text-xs font-medium text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">{count} leads</span>
    </div>
  );
}

// ── Trade Activity Row ────────────────────────────────────────────────────────
function TradeRow({ name, count, total }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  const color = TRADE_COLORS[name] || '#1d4ed8';
  const emoji = TRADE_EMOJI[name] || '📋';
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 text-sm font-medium text-gray-700 truncate">{emoji} {name}</span>
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}/>
      </div>
      <span className="w-8 text-right text-sm font-semibold text-gray-700">{count}</span>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [recentLeads, setRecentLeads] = useState([]);
  const [hotLeads, setHotLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true); setError(null);
      try {
        const [dashData, allLeads] = await Promise.all([
          getDashboard(),
          getLeads({ limit: 40, sort_by: 'score' }),
        ]);
        setStats(dashData);
        const leads = Array.isArray(allLeads) ? allLeads : (allLeads.data || []);
        // Hot leads: top scored
        setHotLeads(leads.slice(0, 6));
        // Recent: last posted
        setRecentLeads([...leads].sort((a, b) => (b.posted || '').localeCompare(a.posted || '')).slice(0, 3));
      } catch (err) { setError(err.message); }
      finally { setLoading(false); }
    }
    fetchData();
  }, []);

  if (loading) return <DashboardSkeleton />;
  if (error) return (
    <div className="rounded-2xl bg-red-50 border border-red-200 p-8 text-center">
      <div className="text-3xl mb-2">⚠️</div>
      <p className="font-semibold text-red-800">Failed to load dashboard</p>
      <p className="text-sm text-red-600 mt-1">{error}</p>
      <button onClick={() => window.location.reload()} className="mt-4 btn-primary">Retry</button>
    </div>
  );

  const totalTrades = Object.values(stats?.by_trade || {}).reduce((a, b) => a + b, 0);

  const tradeBarData = stats?.by_trade
    ? Object.entries(stats.by_trade).map(([name, value]) => ({
        name: name.charAt(0) + name.slice(1).toLowerCase(), value,
        fill: TRADE_COLORS[name] || '#1d4ed8',
      }))
    : [];

  const valueRangeData = [
    { name: 'Under $50k', value: stats?.by_value_range?.under_50k || 0 },
    { name: '$50k–$200k', value: stats?.by_value_range?.['50k_200k'] || 0 },
    { name: 'Over $200k', value: stats?.by_value_range?.over_200k || 0 },
  ];

  const typeData = stats?.by_type
    ? Object.entries(stats.by_type).map(([k, v]) => ({ name: k.charAt(0).toUpperCase()+k.slice(1), value: v }))
    : [];

  const newWeek = stats?.new_this_week || 0;
  const newToday = stats?.new_today || 0;

  return (
    <div className="space-y-6">
      {/* Hero stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon="🏗️" label="Total Leads" value={stats?.total_leads?.toLocaleString() || '0'}
          sub={`${newToday} new today`}
          gradient="bg-gradient-to-br from-blue-600 to-blue-800"
          trend={`+${newWeek} this week`}
        />
        <StatCard
          icon="💰" label="Pipeline Value" value={fmt(stats?.total_value || 0)}
          sub="Across all active leads"
          gradient="bg-gradient-to-br from-emerald-500 to-emerald-700"
        />
        <StatCard
          icon="⭐" label="Avg Score" value={stats?.avg_score || '--'}
          sub="Lead quality index"
          gradient="bg-gradient-to-br from-amber-500 to-orange-600"
          trend={stats?.avg_score >= 75 ? '🔥 Hot market' : '📈 Growing'}
        />
        <StatCard
          icon="👷" label="Contractors" value={stats?.total_contractors?.toLocaleString() || '0'}
          sub="Licensed & tracked"
          gradient="bg-gradient-to-br from-purple-600 to-purple-800"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trade breakdown bar */}
        <div className="lg:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">Leads by Trade</h2>
            <Link to="/leads" className="text-xs text-primary-600 hover:underline">View all →</Link>
          </div>
          <div className="space-y-3">
            {Object.entries(stats?.by_trade || {}).slice(0, 6).map(([name, count]) => (
              <TradeRow key={name} name={name} count={count} total={totalTrades} />
            ))}
          </div>
        </div>

        {/* Value distribution */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Value Distribution</h2>
          <ChartWidget type="pie" data={valueRangeData} height={180} />
          <div className="mt-3 space-y-1.5">
            {valueRangeData.map(({ name, value }) => (
              <div key={name} className="flex justify-between text-xs">
                <span className="text-gray-600">{name}</span>
                <span className="font-semibold text-gray-800">{value} leads</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Hot leads + Markets row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Hot leads feed */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
              🔥 Hottest Leads
              <span className="text-xs font-normal text-gray-500">by score</span>
            </h2>
            <Link to="/leads" className="text-sm font-medium text-primary-600 hover:underline">
              Browse all {stats?.total_leads || ''} →
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {hotLeads.map(lead => <LeadCard key={lead.id} lead={lead} />)}
          </div>
        </div>

        {/* Right column: markets + type split */}
        <div className="space-y-4">
          {/* Hot markets */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
              📍 Hottest Markets
            </h2>
            <div>
              {(stats?.hot_markets || []).slice(0, 6).map((m, i) => (
                <HotMarketBadge key={m.city} city={m.city} count={m.count} rank={i} />
              ))}
            </div>
          </div>

          {/* Permit vs Bid split */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Lead Source Mix</h2>
            <ChartWidget type="pie" data={typeData} height={120} />
            <div className="mt-2 flex justify-center gap-4">
              {typeData.map(({ name, value }) => (
                <div key={name} className="text-center">
                  <div className="text-lg font-bold text-gray-800">{value}</div>
                  <div className="text-xs text-gray-500">{name}s</div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick actions */}
          <div className="card p-5 space-y-2">
            <h2 className="text-sm font-semibold text-gray-900 mb-1">Quick Actions</h2>
            <Link to="/leads?sort_by=score" className="flex items-center gap-2 w-full rounded-lg bg-primary-50 hover:bg-primary-100 px-3 py-2 text-sm font-medium text-primary-700 transition-colors">
              🔥 Top Scored Leads
            </Link>
            <Link to="/leads?type=bid" className="flex items-center gap-2 w-full rounded-lg bg-amber-50 hover:bg-amber-100 px-3 py-2 text-sm font-medium text-amber-700 transition-colors">
              📋 Federal Bids Only
            </Link>
            <Link to="/pipeline" className="flex items-center gap-2 w-full rounded-lg bg-emerald-50 hover:bg-emerald-100 px-3 py-2 text-sm font-medium text-emerald-700 transition-colors">
              📊 My Pipeline
            </Link>
            <Link to="/maps" className="flex items-center gap-2 w-full rounded-lg bg-purple-50 hover:bg-purple-100 px-3 py-2 text-sm font-medium text-purple-700 transition-colors">
              🗺️ Market Map
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
