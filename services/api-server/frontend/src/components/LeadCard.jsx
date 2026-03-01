import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import { MapPin, Phone, Clock, ChevronRight, Bookmark } from 'lucide-react'

function fmtVal(v) {
  if (!v && v !== 0) return '—'
  if (v >= 1e9) return `$${(v/1e9).toFixed(1)}B`
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`
  if (v >= 1e3) return `$${Math.round(v/1e3)}K`
  return `$${v}`
}
function relDate(s) {
  if (!s) return null
  try { return formatDistanceToNow(new Date(s), { addSuffix: true }) } catch { return null }
}

const TRADE_STYLE = (t) => {
  const m = {
    ELECTRICAL:      'bg-amber-50 text-amber-700',
    PLUMBING:        'bg-sky-50 text-sky-700',
    HVAC:            'bg-teal-50 text-teal-700',
    ROOFING:         'bg-orange-50 text-orange-700',
    CONCRETE:        'bg-stone-50 text-stone-600',
    GENERAL:         'bg-violet-50 text-violet-700',
    FIRE_PROTECTION: 'bg-red-50 text-red-700',
  }
  return m[t] ?? 'bg-gray-50 text-gray-600'
}

const scoreLabel = s => s >= 80 ? 'Hot' : s >= 60 ? 'Good' : s >= 40 ? 'Fair' : 'Low'
const scoreStyle = s =>
  s >= 80 ? 'text-emerald-600' : s >= 60 ? 'text-blue-600' : s >= 40 ? 'text-amber-600' : 'text-gray-400'

export default function LeadCard({ lead, compact = false }) {
  const owner = lead.owner || {}
  const score = lead.score || 0

  const handleSave = async (e) => {
    e.preventDefault(); e.stopPropagation()
    let email = localStorage.getItem('pipeline_email')
    if (!email) {
      email = window.prompt('Enter your email to save this lead:')
      if (!email) return
      localStorage.setItem('pipeline_email', email.trim())
    }
    await fetch(`/api/pipeline/leads/${lead.id}/save`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_email: email }),
    })
  }

  return (
    <Link to={`/leads/${lead.id}`}
      className={clsx('group block rounded-card bg-white shadow-card hover:shadow-card-hover transition-shadow', compact ? 'p-3' : 'p-4')}>
      {/* Top */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className={clsx('inline-flex items-center rounded px-2 py-0.5 text-[11px] font-medium', TRADE_STYLE(lead.trade))}>
            {lead.trade || 'GENERAL'}
          </span>
          <span className="inline-flex items-center rounded px-2 py-0.5 text-[11px] font-medium bg-gray-50 text-gray-400 capitalize">
            {lead.type || 'permit'}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={clsx('text-xs font-bold tabular-nums', scoreStyle(score))}>
            {score} <span className="font-normal text-gray-400 text-[10px]">{scoreLabel(score)}</span>
          </span>
          <button onClick={handleSave} className="text-gray-200 hover:text-primary-700 transition-colors">
            <Bookmark className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Title */}
      <p className={clsx('font-medium text-gray-900 group-hover:text-primary-700 line-clamp-2', compact ? 'text-xs' : 'text-sm')}>
        {lead.title}
      </p>

      {/* Value */}
      <p className={clsx('font-bold text-gray-900 mt-1.5', compact ? 'text-sm' : 'text-base')}>
        {fmtVal(lead.value)}
      </p>

      {!compact && (
        <div className="mt-2 space-y-1 text-xs text-gray-400">
          {lead.addr && <div className="flex items-center gap-1.5"><MapPin className="h-3 w-3 shrink-0" /><span className="truncate">{lead.addr}</span></div>}
          {owner.p && <a href={`tel:${owner.p}`} onClick={e => e.stopPropagation()} className="flex items-center gap-1.5 hover:text-primary-700"><Phone className="h-3 w-3 shrink-0" />{owner.p}</a>}
          {lead.posted && <div className="flex items-center gap-1.5"><Clock className="h-3 w-3 shrink-0" />{relDate(lead.posted)}</div>}
        </div>
      )}

      {!compact && (
        <div className="mt-3 flex items-center justify-between border-t border-gray-50 pt-2.5">
          <span className="text-[11px] text-gray-400 truncate max-w-[65%]">
            {lead.gc?.n ? `GC: ${lead.gc.n}` : lead.src || '—'}
          </span>
          <span className="text-xs text-primary-700 font-medium flex items-center gap-0.5 group-hover:gap-1 transition-all">
            View <ChevronRight className="h-3.5 w-3.5" />
          </span>
        </div>
      )}
    </Link>
  )
}
