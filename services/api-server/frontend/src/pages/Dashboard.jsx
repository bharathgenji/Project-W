import { useEffect, useState, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { formatDistanceToNow, format } from 'date-fns'
import { ArrowRight, RefreshCw, CheckCircle2, Loader2, MapPin, Clock } from 'lucide-react'
import toast from 'react-hot-toast'
import { getDashboard, getLeads, getIngestStatus, runIngest } from '../api/client'

// ── helpers ───────────────────────────────────────────────────────────────────
function fmtVal(v) {
  if (!v && v !== 0) return '—'
  if (v >= 1e12) return `$${(v/1e12).toFixed(1)}T`
  if (v >= 1e9) return `$${(v/1e9).toFixed(1)}B`
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`
  if (v >= 1e3) return `$${Math.round(v/1e3)}K`
  return `$${v}`
}
function relDate(s) {
  if (!s) return null
  try { return formatDistanceToNow(new Date(s), { addSuffix: true }) } catch { return null }
}
const TRADE_COLOR = (t) => {
  const map = {
    ELECTRICAL:'bg-amber-50 text-amber-700 border border-amber-100',
    PLUMBING:  'bg-sky-50 text-sky-700 border border-sky-100',
    HVAC:      'bg-teal-50 text-teal-700 border border-teal-100',
    ROOFING:   'bg-orange-50 text-orange-700 border border-orange-100',
    CONCRETE:  'bg-stone-50 text-stone-600 border border-stone-100',
    GENERAL:   'bg-violet-50 text-violet-700 border border-violet-100',
    FIRE_PROTECTION: 'bg-red-50 text-red-700 border border-red-100',
  }
  return map[t] ?? 'bg-gray-50 text-gray-600 border border-gray-100'
}

// ── Stat card — number-first, no colored icon boxes ───────────────────────────
function StatCard({ label, value, sub, accent }) {
  return (
    <div className="rounded-card bg-white shadow-card px-5 py-4 border-t-2" style={{ borderTopColor: accent || '#1E3A5F' }}>
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900 tracking-tight">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

function StatSkeleton() {
  return (
    <div className="rounded-card bg-white shadow-card px-5 py-4 border-t-2 border-gray-100 animate-pulse">
      <div className="h-3 w-20 bg-gray-100 rounded mb-2" />
      <div className="h-7 w-24 bg-gray-100 rounded" />
      <div className="h-3 w-28 bg-gray-100 rounded mt-2" />
    </div>
  )
}

// ── Lead row — plain table row, no colored backgrounds ────────────────────────
function LeadRow({ lead }) {
  return (
    <Link to={`/leads/${lead.id}`}
      className="grid grid-cols-[1fr_90px_72px_56px_90px] items-center gap-2 px-4 py-3 hover:bg-gray-50 transition-colors group text-sm border-b border-gray-50 last:border-0">
      <div className="min-w-0">
        <p className="font-medium text-gray-900 truncate group-hover:text-primary-700">{lead.title}</p>
        {lead.addr && (
          <p className="mt-0.5 flex items-center gap-1 text-xs text-gray-400 truncate">
            <MapPin className="h-3 w-3 shrink-0" />{lead.addr}
          </p>
        )}
      </div>
      <span className={clsx('inline-flex items-center justify-center rounded px-2 py-0.5 text-xs font-medium truncate', TRADE_COLOR(lead.trade))}>
        {lead.trade}
      </span>
      <span className="text-sm font-semibold text-gray-900 text-right">{fmtVal(lead.value)}</span>
      <span className={clsx('text-xs font-bold text-right tabular-nums',
        lead.score >= 70 ? 'text-emerald-600' : lead.score >= 45 ? 'text-amber-600' : 'text-gray-400')}>
        {lead.score ?? '—'}
      </span>
      <span className="text-xs text-gray-400 text-right">{relDate(lead.posted) || '—'}</span>
    </Link>
  )
}

// ── Trade bar — single navy color, clean ──────────────────────────────────────
function TradeBar({ name, count, total }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="w-28 text-xs text-gray-600 truncate">{name}</span>
      <div className="flex-1 h-1 rounded-full bg-gray-100 overflow-hidden">
        <div className="h-full rounded-full bg-primary-700 opacity-70" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-xs font-semibold text-gray-700 tabular-nums">{count}</span>
    </div>
  )
}

// ── Ingest header row ────────────────────────────────────────────────────────
function IngestBar({ status, onRefresh }) {
  const running = status?.running
  const lastRun = status?.last_run
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h1 className="text-lg font-semibold text-gray-900">Dashboard</h1>
        <p className="mt-0.5 text-sm text-gray-400">
          {running ? (
            <span className="flex items-center gap-1.5 text-blue-600">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Fetching live data from Socrata + SAM.gov…
            </span>
          ) : lastRun ? (
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              Updated {formatDistanceToNow(new Date(lastRun), { addSuffix: true })} · {format(new Date(lastRun), 'MMM d, h:mm a')}
            </span>
          ) : 'No data ingested yet — click Refresh to pull live permits.'}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <button onClick={onRefresh} disabled={running}
          className={clsx('btn btn-secondary btn-sm flex items-center gap-1.5', running && 'opacity-50 cursor-not-allowed')}>
          <RefreshCw className={clsx('h-3.5 w-3.5', running && 'animate-spin')} />
          {running ? 'Running…' : 'Refresh Data'}
        </button>
        <Link to="/leads" className="btn btn-primary btn-sm flex items-center gap-1.5">
          All Leads <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [hotLeads, setHotLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [ingestStatus, setIngestStatus] = useState(null)
  const pollRef = useRef(null)

  const fetchDashboard = useCallback(async () => {
    setLoading(true)
    const [s, env] = await Promise.all([
      getDashboard(),
      getLeads({ limit: 10, sort_by: 'score' }),
    ])
    setStats(s)
    setHotLeads(Array.isArray(env) ? env : (env.data || []))
    setLoading(false)
  }, [])

  const fetchIngestStatus = useCallback(async () => {
    try { const s = await getIngestStatus(); setIngestStatus(s); return s } catch { return null }
  }, [])

  const startPolling = useCallback(() => {
    if (pollRef.current) return
    pollRef.current = setInterval(async () => {
      const s = await fetchIngestStatus()
      if (s && !s.running) {
        clearInterval(pollRef.current); pollRef.current = null
        setLoading(true); await fetchDashboard()
        toast.success(`Done — ${s.last_run_leads?.toLocaleString() ?? 0} leads loaded`)
      }
    }, 3000)
  }, [fetchIngestStatus, fetchDashboard])

  const handleRefresh = async () => {
    try {
      const r = await runIngest(30, 500)
      if (r.status === 'already_running') { toast('Already running', { icon: 'ℹ️' }); return }
      toast.success('Fetching live data — ~2 min')
      setIngestStatus(s => ({ ...s, running: true }))
      startPolling()
    } catch { toast.error('Could not start ingestion') }
  }

  useEffect(() => {
    fetchDashboard(); fetchIngestStatus()
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [fetchDashboard, fetchIngestStatus])

  const totalTrades = Object.values(stats?.by_trade || {}).reduce((a, b) => a + b, 0)

  return (
    <div className="space-y-6 max-w-6xl">
      <IngestBar status={ingestStatus} onRefresh={handleRefresh} />

      {/* Stat cards — top-border accent, number-first */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {loading ? [0,1,2,3].map(i => <StatSkeleton key={i} />) : <>
          <StatCard label="Active Leads" value={(stats?.total_leads ?? 0).toLocaleString()}
            sub={stats?.new_today ? `${stats.new_today} new today` : `${stats?.new_this_week ?? 0} this week`}
            accent="#1E3A5F" />
          <StatCard label="Pipeline Value" value={fmtVal(stats?.total_value || 0)}
            sub="permits + federal bids" accent="#059669" />
          <StatCard label="Avg Lead Score" value={stats?.avg_score ?? '—'}
            sub="out of 100" accent="#D97706" />
          <StatCard label="Contractors" value={(stats?.total_contractors ?? 0).toLocaleString()}
            sub="licensed & tracked" accent="#7C3AED" />
        </>}
      </div>

      {/* Main 2-col grid */}
      <div className="grid gap-5 lg:grid-cols-3">
        {/* Leads table — 2 cols */}
        <div className="lg:col-span-2 rounded-card bg-white shadow-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
            <h2 className="text-sm font-semibold text-gray-900">Top Leads</h2>
            <Link to="/leads?sort_by=score" className="text-xs text-secondary hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {/* Column headers */}
          <div className="grid grid-cols-[1fr_90px_72px_56px_90px] gap-2 px-4 py-2 border-b border-gray-100 bg-gray-50">
            {['Lead', 'Trade', 'Value', 'Score', 'Posted'].map(h => (
              <span key={h} className="text-xs font-medium text-gray-400 uppercase tracking-wide last:text-right">{h}</span>
            ))}
          </div>
          <div>
            {loading
              ? [0,1,2,3,4].map(i => (
                  <div key={i} className="flex items-center gap-4 px-4 py-3 border-b border-gray-50 animate-pulse">
                    <div className="flex-1 space-y-1.5"><div className="h-3.5 w-3/4 bg-gray-100 rounded" /><div className="h-3 w-1/2 bg-gray-100 rounded" /></div>
                    <div className="h-5 w-20 bg-gray-100 rounded" />
                  </div>
                ))
              : hotLeads.map(l => <LeadRow key={l.id} lead={l} />)
            }
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-5">
          {/* By trade */}
          <div className="rounded-card bg-white shadow-card overflow-hidden">
            <div className="border-b border-gray-100 px-4 py-3">
              <h2 className="text-sm font-semibold text-gray-900">Leads by Trade</h2>
            </div>
            <div className="px-4 py-3">
              {loading
                ? [0,1,2,3].map(i => <div key={i} className="h-3 my-2.5 bg-gray-100 rounded animate-pulse" />)
                : Object.entries(stats?.by_trade || {}).slice(0, 8).map(([name, count]) => (
                    <TradeBar key={name} name={name} count={count} total={totalTrades} />
                  ))
              }
            </div>
          </div>

          {/* Hot markets */}
          <div className="rounded-card bg-white shadow-card overflow-hidden">
            <div className="border-b border-gray-100 px-4 py-3">
              <h2 className="text-sm font-semibold text-gray-900">Hot Markets</h2>
            </div>
            <div>
              {(stats?.hot_markets || []).slice(0, 6).map((m, i) => (
                <div key={m.city} className="flex items-center gap-3 px-4 py-2.5 border-b border-gray-50 last:border-0">
                  <span className="text-xs font-bold text-gray-300 w-4 tabular-nums">{i + 1}</span>
                  <MapPin className="h-3.5 w-3.5 text-gray-300 shrink-0" />
                  <span className="flex-1 text-sm text-gray-700">{m.city}</span>
                  <span className="text-xs font-semibold text-gray-500 tabular-nums">{m.count}</span>
                </div>
              ))}
              {loading && [0,1,2,3].map(i => (
                <div key={i} className="flex items-center gap-3 px-4 py-2.5 animate-pulse">
                  <div className="h-3 w-full bg-gray-100 rounded" />
                </div>
              ))}
            </div>
          </div>

          {/* Type split */}
          <div className="rounded-card bg-white shadow-card overflow-hidden">
            <div className="border-b border-gray-100 px-4 py-3">
              <h2 className="text-sm font-semibold text-gray-900">Lead Sources</h2>
            </div>
            <div className="px-4 py-3 space-y-2">
              {!loading && <>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">City Permits</span>
                  <span className="font-semibold text-gray-900 tabular-nums">{(stats?.by_type?.permit || 0).toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Federal Bids</span>
                  <span className="font-semibold text-gray-900 tabular-nums">{(stats?.by_type?.bid || 0).toLocaleString()}</span>
                </div>
                <div className="mt-2 flex items-center gap-1 text-xs text-gray-400">
                  <Clock className="h-3 w-3" />
                  {stats?.new_this_week ?? 0} new leads this week
                </div>
              </>}
              {loading && <div className="h-16 bg-gray-50 rounded animate-pulse" />}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
