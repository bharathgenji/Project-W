import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import { MapPin, Clock, ChevronRight, Bookmark, DollarSign } from 'lucide-react'

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

// Score ring color — single accent, no rainbow
function scoreColor(s) {
  if (s >= 70) return '#1E3A5F'   // navy — hot
  if (s >= 50) return '#3B6EA8'   // medium blue
  return '#9CA3AF'                // gray — low
}

function ScoreBadge({ score, compact }) {
  const color = scoreColor(score)
  const label = score >= 70 ? 'Hot' : score >= 50 ? 'Good' : score >= 30 ? 'Fair' : 'Low'
  return (
    <div className="flex flex-col items-center shrink-0">
      <svg width={compact ? 30 : 36} height={compact ? 30 : 36} viewBox="0 0 36 36">
        <circle cx="18" cy="18" r="15" fill="none" stroke="#F3F4F6" strokeWidth="3" />
        <circle
          cx="18" cy="18" r="15" fill="none"
          stroke={color} strokeWidth="3"
          strokeDasharray={`${(score / 100) * 94.2} 94.2`}
          strokeLinecap="round"
          transform="rotate(-90 18 18)"
        />
        <text x="18" y="22" textAnchor="middle" fontSize={compact ? "9" : "10"} fontWeight="700" fill="#111827">
          {score}
        </text>
      </svg>
      {!compact && <span className="text-[9px] text-gray-400 mt-0.5 font-medium">{label}</span>}
    </div>
  )
}

export default function LeadCard({ lead, compact = false }) {
  const score = lead.score || 0
  const trade = lead.trade || 'GENERAL'
  const tradeLabel = trade.replace(/_/g, ' ')

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
    <Link
      to={`/leads/${lead.id}`}
      className={clsx(
        'group block rounded-card bg-white shadow-card hover:shadow-card-hover transition-shadow border border-gray-100',
        compact ? 'p-3' : 'p-4'
      )}
    >
      {/* Top row: badges + score ring */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 flex-wrap min-w-0">
          {/* Trade badge — neutral, no color coding */}
          <span className="inline-flex items-center rounded px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase bg-primary-50 text-primary-700">
            {tradeLabel}
          </span>
          <span className="inline-flex items-center rounded px-2 py-0.5 text-[10px] font-medium text-gray-400 bg-gray-50 capitalize">
            {lead.type || 'permit'}
          </span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={handleSave}
            className="text-gray-200 hover:text-primary-700 transition-colors p-0.5"
            title="Save lead"
          >
            <Bookmark className="h-3.5 w-3.5" />
          </button>
          <ScoreBadge score={score} compact={compact} />
        </div>
      </div>

      {/* Title */}
      <p className={clsx(
        'font-medium text-gray-900 group-hover:text-primary-700 line-clamp-2 transition-colors',
        compact ? 'text-xs' : 'text-sm'
      )}>
        {lead.title}
      </p>

      {/* Value */}
      {lead.value > 0 && (
        <div className="flex items-center gap-1 mt-1.5">
          <DollarSign className="h-3.5 w-3.5 text-gray-400 shrink-0" />
          <span className={clsx('font-bold text-gray-900', compact ? 'text-sm' : 'text-base')}>
            {fmtVal(lead.value)}
          </span>
        </div>
      )}

      {!compact && (
        <div className="mt-2 space-y-1 text-xs text-gray-400">
          {lead.addr && (
            <div className="flex items-center gap-1.5">
              <MapPin className="h-3 w-3 shrink-0" />
              <span className="truncate">{lead.addr}</span>
            </div>
          )}
          {lead.posted && (
            <div className="flex items-center gap-1.5">
              <Clock className="h-3 w-3 shrink-0" />
              <span>{relDate(lead.posted)}</span>
            </div>
          )}
        </div>
      )}

      {!compact && (
        <div className="mt-3 flex items-center justify-between border-t border-gray-50 pt-2.5">
          <span className="text-[11px] text-gray-400 truncate max-w-[65%]">
            {lead.gc?.n ? `GC: ${lead.gc.n}` : (lead.city ? `${lead.city}` : lead.src || '—')}
          </span>
          <span className="text-xs text-primary-700 font-medium flex items-center gap-0.5 group-hover:gap-1.5 transition-all">
            View <ChevronRight className="h-3.5 w-3.5" />
          </span>
        </div>
      )}
    </Link>
  )
}
