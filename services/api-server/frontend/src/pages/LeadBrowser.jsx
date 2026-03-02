import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import { Search, Filter, Download, ChevronLeft, ChevronRight, MapPin, Clock, LayoutGrid, List, X } from 'lucide-react'
import { getLeads } from '../api/client'
import LeadCard from '../components/LeadCard'

function fmtVal(v) {
  if (!v && v !== 0) return '—'
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`
  if (v >= 1e3) return `$${Math.round(v/1e3)}K`
  return `$${v}`
}
function relDate(s) {
  try { return formatDistanceToNow(new Date(s), { addSuffix: true }) } catch { return s }
}

const TRADES = ['ELECTRICAL','PLUMBING','HVAC','ROOFING','CONCRETE','FRAMING','DRYWALL','PAINTING','FLOORING','GENERAL','DEMOLITION','FIRE_PROTECTION','SOLAR','SITE_WORK']

const CITIES = [
  { label: 'Chicago, IL',       src: 'chicago' },
  { label: 'Austin, TX',        src: 'austin' },
  { label: 'San Francisco, CA', src: 'sf' },
  { label: 'New York City, NY', src: 'nyc' },
  { label: 'Los Angeles, CA',   src: 'los-angeles' },
  { label: 'Seattle, WA',       src: 'seattle' },
  { label: 'New Orleans, LA',   src: 'new-orleans' },
  { label: 'Dallas, TX',        src: 'dallas' },
  { label: 'San Antonio, TX',   src: 'san-antonio' },
  { label: 'Boston, MA',        src: 'boston' },
  { label: 'Nashville, TN',    src: 'nashville' },
  { label: 'Portland, OR',     src: 'portland' },
  { label: 'Federal (SAM.gov)',src: 'sam' },
  { label: 'Federal (Awards)', src: 'usaspending' },
]
// Uniform trade badge — no per-trade color coding
const tradeBadge = () => 'bg-primary-50 text-primary-700'
const SCORE_COLOR = s => s >= 70 ? 'text-primary-700 font-bold' : s >= 50 ? 'text-gray-700 font-semibold' : 'text-gray-400'

// ── Table row ─────────────────────────────────────────────────────────────────
function LeadTableRow({ lead }) {
  return (
    <tr className="group border-b border-gray-100 hover:bg-gray-50 transition-colors">
      <td className="py-3 pl-4 pr-3">
        <Link to={`/leads/${lead.id}`} className="block">
          <p className="text-sm font-medium text-gray-900 group-hover:text-primary-700 line-clamp-1">{lead.title}</p>
          {lead.addr && (
            <p className="mt-0.5 flex items-center gap-1 text-xs text-gray-400">
              <MapPin className="h-3 w-3 shrink-0" />{lead.addr}
            </p>
          )}
        </Link>
      </td>
      <td className="py-3 px-3">
        <span className={clsx('inline-flex items-center rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide', tradeBadge())}>
          {(lead.trade || 'GENERAL').replace(/_/g, ' ')}
        </span>
      </td>
      <td className="py-3 px-3">
        <span className="text-sm font-semibold text-gray-900">{fmtVal(lead.value)}</span>
      </td>
      <td className="py-3 px-3">
        <span className={clsx('text-sm font-bold', SCORE_COLOR(lead.score || 0))}>{lead.score || '—'}</span>
      </td>
      <td className="py-3 px-3 text-xs text-gray-400 capitalize">{lead.type || 'permit'}</td>
      <td className="py-3 pl-3 pr-4 text-xs text-gray-400">
        {lead.posted ? <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{relDate(lead.posted)}</span> : '—'}
      </td>
    </tr>
  )
}

// ── Filters ───────────────────────────────────────────────────────────────────
function FilterPanel({ filters, onChange, onClose }) {
  return (
    <aside className="w-56 shrink-0 space-y-5">
      <div className="rounded-card bg-white shadow-card p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
          {onClose && <button onClick={onClose} className="text-gray-400 hover:text-gray-600 lg:hidden"><X className="h-4 w-4" /></button>}
        </div>

        {/* Trade */}
        <div className="mb-4">
          <label className="mb-1.5 block text-xs font-medium text-gray-500 uppercase tracking-wide">Trade</label>
          <div className="space-y-1">
            {TRADES.map(t => (
              <label key={t} className="flex items-center gap-2 cursor-pointer group">
                <input type="checkbox" className="rounded border-gray-300 text-primary-700 focus:ring-primary-700"
                  checked={filters.trades?.includes(t) || false}
                  onChange={e => {
                    const cur = filters.trades || []
                    onChange('trades', e.target.checked ? [...cur, t] : cur.filter(x => x !== t))
                  }} />
                <span className="text-sm text-gray-600 group-hover:text-gray-900">{t}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Type */}
        <div className="mb-4">
          <label className="mb-1.5 block text-xs font-medium text-gray-500 uppercase tracking-wide">Type</label>
          <div className="space-y-1">
            {['permit', 'bid'].map(t => (
              <label key={t} className="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="type" className="border-gray-300 text-primary-700 focus:ring-primary-700"
                  checked={filters.type === t} onChange={() => onChange('type', t)} />
                <span className="text-sm text-gray-600 capitalize">{t}s</span>
              </label>
            ))}
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="type" className="border-gray-300 text-primary-700 focus:ring-primary-700"
                checked={!filters.type} onChange={() => onChange('type', '')} />
              <span className="text-sm text-gray-600">All</span>
            </label>
          </div>
        </div>

        {/* City */}
        <div className="mb-4">
          <label className="mb-1.5 block text-xs font-medium text-gray-500 uppercase tracking-wide">City</label>
          <select value={filters.src || ''}
            onChange={e => onChange('src', e.target.value)}
            className="input-base text-xs py-1.5">
            <option value="">All cities</option>
            {CITIES.map(c => <option key={c.src} value={c.src}>{c.label}</option>)}
          </select>
        </div>

        {/* Sort */}
        <div>
          <label className="mb-1.5 block text-xs font-medium text-gray-500 uppercase tracking-wide">Sort by</label>
          <select value={filters.sort_by || 'score'}
            onChange={e => onChange('sort_by', e.target.value)}
            className="input-base text-xs py-1.5">
            <option value="score">Score</option>
            <option value="value">Value</option>
            <option value="posted_date">Newest First</option>
          </select>
        </div>

        {/* Clear */}
        {(filters.trades?.length || filters.type || filters.src || filters.sort_by !== 'score') && (
          <button onClick={() => onChange('_reset')} className="mt-3 text-xs text-secondary hover:underline">
            Clear all filters
          </button>
        )}
      </div>
    </aside>
  )
}

const PAGE_SIZE = 20

export default function LeadBrowser() {
  const [leads, setLeads] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState('table') // 'table' | 'grid'
  const [search, setSearch] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState({ trades: [], type: '', sort_by: 'score' })

  const fetchLeads = useCallback(async () => {
    setLoading(true)
    try {
      const params = { limit: PAGE_SIZE, offset: page * PAGE_SIZE, sort_by: filters.sort_by || 'score' }
      if (search) params.q = search
      if (filters.src) params.src = filters.src
      if (filters.type) params.type = filters.type
      if (filters.trades?.length === 1) params.trade = filters.trades[0]
      const env = await getLeads(params)
      const data = Array.isArray(env) ? env : (env.data || [])
      setLeads(data)
      setTotal(env.total || data.length)
    } finally { setLoading(false) }
  }, [page, filters, search])

  useEffect(() => { fetchLeads() }, [fetchLeads])

  const handleFilter = (key, val) => {
    if (key === '_reset') { setFilters({ trades: [], type: '', src: '', sort_by: 'score' }); setPage(0); return }
    setFilters(f => ({ ...f, [key]: val }))
    setPage(0)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)
  const activeFilterCount = (filters.trades?.length || 0) + (filters.type ? 1 : 0) + (filters.src ? 1 : 0)

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Leads</h1>
          <p className="mt-0.5 text-sm text-gray-500">{total.toLocaleString()} results</p>
        </div>
        <div className="flex items-center gap-2">
          <a href="/api/leads/export" className="btn btn-secondary btn-sm flex items-center gap-1.5 text-xs">
            <Download className="h-3.5 w-3.5" /> Export CSV
          </a>
          <button onClick={() => setShowFilters(f => !f)}
            className={clsx('btn btn-secondary btn-sm flex items-center gap-1.5 text-xs lg:hidden', showFilters && 'bg-primary-50 border-primary-300 text-primary-700')}>
            <Filter className="h-3.5 w-3.5" />
            Filters {activeFilterCount > 0 && <span className="rounded-full bg-primary-700 text-white text-[10px] w-4 h-4 flex items-center justify-center">{activeFilterCount}</span>}
          </button>
          <div className="hidden sm:flex items-center rounded-lg border border-gray-200 bg-white p-0.5">
            <button onClick={() => setView('table')} className={clsx('rounded p-1.5 transition-colors', view === 'table' ? 'bg-gray-100 text-gray-900' : 'text-gray-400 hover:text-gray-700')}>
              <List className="h-4 w-4" />
            </button>
            <button onClick={() => setView('grid')} className={clsx('rounded p-1.5 transition-colors', view === 'grid' ? 'bg-gray-100 text-gray-900' : 'text-gray-400 hover:text-gray-700')}>
              <LayoutGrid className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Search bar */}
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(0) }}
          placeholder="Search by title, address, trade…"
          className="input-base pl-10" />
      </div>

      <div className="flex gap-5 items-start">
        {/* Filters — desktop always visible, mobile toggle */}
        <div className={clsx('shrink-0', showFilters ? 'block' : 'hidden lg:block')}>
          <FilterPanel filters={filters} onChange={handleFilter} onClose={() => setShowFilters(false)} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {loading ? (
            <div className="rounded-card bg-white shadow-card">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="flex items-center gap-4 p-4 border-b border-gray-50 animate-pulse">
                  <div className="flex-1 space-y-1.5">
                    <div className="h-3.5 w-3/4 bg-gray-100 rounded" />
                    <div className="h-3 w-1/2 bg-gray-100 rounded" />
                  </div>
                  <div className="h-5 w-24 bg-gray-100 rounded" />
                </div>
              ))}
            </div>
          ) : leads.length === 0 ? (
            <div className="rounded-card bg-white shadow-card flex flex-col items-center justify-center py-16 text-center">
              <Search className="h-10 w-10 text-gray-200 mb-3" />
              <p className="font-medium text-gray-700">No leads found</p>
              <p className="text-sm text-gray-400 mt-1">Try adjusting your filters or search query</p>
            </div>
          ) : view === 'grid' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
              {leads.map(l => <LeadCard key={l.id} lead={l} />)}
            </div>
          ) : (
            <div className="rounded-card bg-white shadow-card overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="py-2.5 pl-4 pr-3 text-left text-xs font-medium text-gray-500">Lead</th>
                    <th className="py-2.5 px-3 text-left text-xs font-medium text-gray-500">Trade</th>
                    <th className="py-2.5 px-3 text-left text-xs font-medium text-gray-500">Value</th>
                    <th className="py-2.5 px-3 text-left text-xs font-medium text-gray-500">Score</th>
                    <th className="py-2.5 px-3 text-left text-xs font-medium text-gray-500">Type</th>
                    <th className="py-2.5 pl-3 pr-4 text-left text-xs font-medium text-gray-500">Posted</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map(l => <LeadTableRow key={l.id} lead={l} />)}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total.toLocaleString()}
              </p>
              <div className="flex items-center gap-2">
                <button onClick={() => setPage(p => p - 1)} disabled={page === 0}
                  className="btn btn-secondary btn-sm flex items-center gap-1 disabled:opacity-40">
                  <ChevronLeft className="h-4 w-4" /> Prev
                </button>
                <button onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}
                  className="btn btn-secondary btn-sm flex items-center gap-1 disabled:opacity-40">
                  Next <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
