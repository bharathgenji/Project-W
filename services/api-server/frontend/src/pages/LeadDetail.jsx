import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { clsx } from 'clsx'
import { format, formatDistanceToNow } from 'date-fns'
import {
  ArrowLeft, MapPin, Phone, Mail, Calendar, Clock, ChevronRight,
  Heart, Bell, ExternalLink, Building2, User, Zap, CheckCircle2, Tag,
} from 'lucide-react'
import { getLead, getLeads } from '../api/client'
import LeadCard from '../components/LeadCard'
import toast from 'react-hot-toast'

function fmtVal(v) {
  if (!v && v !== 0) return '—'
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`
  if (v >= 1e3) return `$${Math.round(v/1e3)}K`
  return `$${Number(v).toLocaleString()}`
}
function fmtDate(s) {
  if (!s) return '—'
  try { return format(new Date(s), 'MMM d, yyyy') } catch { return s }
}
function relDate(s) {
  if (!s) return null
  try { return formatDistanceToNow(new Date(s), { addSuffix: true }) } catch { return null }
}

const TRADE_BADGE = {
  ELECTRICAL:'bg-amber-100 text-amber-700', PLUMBING:'bg-blue-100 text-blue-700',
  HVAC:'bg-cyan-100 text-cyan-700', ROOFING:'bg-orange-100 text-orange-700',
  CONCRETE:'bg-gray-100 text-gray-700', GENERAL:'bg-violet-100 text-violet-700',
}

// ── Section wrapper ───────────────────────────────────────────────────────────
function Section({ title, icon: Icon, children }) {
  return (
    <div className="rounded-card bg-white shadow-card overflow-hidden">
      <div className="flex items-center gap-2 border-b border-gray-100 px-5 py-3.5">
        {Icon && <Icon className="h-4 w-4 text-gray-400" />}
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  )
}

// ── Detail row ────────────────────────────────────────────────────────────────
function DetailRow({ label, value, accent }) {
  if (!value) return null
  return (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-gray-50 last:border-0">
      <span className="text-xs text-gray-400 shrink-0 w-28">{label}</span>
      <span className={clsx('text-sm text-right', accent ? 'font-semibold text-gray-900' : 'text-gray-700')}>{value}</span>
    </div>
  )
}

// ── Score ring (SVG) ──────────────────────────────────────────────────────────
function ScoreGauge({ score }) {
  const color = score >= 80 ? '#10b981' : score >= 60 ? '#3b82f6' : score >= 40 ? '#f59e0b' : '#9ca3af'
  const label = score >= 80 ? 'Hot' : score >= 60 ? 'Good' : score >= 40 ? 'Fair' : 'Low'
  const r = 26; const circ = 2 * Math.PI * r; const dash = (score / 100) * circ
  return (
    <div className="flex flex-col items-center">
      <svg width="72" height="72" viewBox="0 0 72 72">
        <circle cx="36" cy="36" r={r} fill="none" stroke="#f3f4f6" strokeWidth="7" />
        <circle cx="36" cy="36" r={r} fill="none" stroke={color} strokeWidth="7"
          strokeDasharray={`${dash} ${circ - dash}`} strokeLinecap="round"
          transform="rotate(-90 36 36)" />
        <text x="36" y="40" textAnchor="middle" fontSize="15" fontWeight="700" fill={color}>{score}</text>
      </svg>
      <span className="text-xs font-semibold mt-0.5" style={{ color }}>{label}</span>
    </div>
  )
}

// ── AI panel ──────────────────────────────────────────────────────────────────
const PT_LABEL = { new_build:'New Construction', renovation:'Renovation', repair:'Repair', addition:'Addition', compliance:'Compliance' }
const OT_LABEL = { residential:'Residential', small_commercial:'Small Commercial', large_commercial:'Large Commercial', institutional:'Institutional' }

function AIPanel({ ai }) {
  if (!ai) return null
  return (
    <Section title="AI Analysis" icon={Zap}>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-400 mb-1">Project Type</p>
          <span className="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium bg-blue-50 text-blue-700">
            {PT_LABEL[ai.project_type] || ai.project_type}
          </span>
        </div>
        <div>
          <p className="text-xs text-gray-400 mb-1">Owner Type</p>
          <span className="inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium bg-purple-50 text-purple-700">
            {OT_LABEL[ai.owner_type] || ai.owner_type}
          </span>
        </div>
        {ai.sqft && <div><p className="text-xs text-gray-400 mb-0.5">Sq Ft</p><p className="text-sm font-semibold text-gray-900">{ai.sqft.toLocaleString()}</p></div>}
        {ai.units && <div><p className="text-xs text-gray-400 mb-0.5">Units</p><p className="text-sm font-semibold text-gray-900">{ai.units}</p></div>}
      </div>
      {ai.key_materials?.length > 0 && (
        <div className="mt-4">
          <p className="text-xs text-gray-400 mb-2">Key Materials</p>
          <div className="flex flex-wrap gap-1.5">
            {ai.key_materials.map((m, i) => (
              <span key={i} className="rounded-md border border-gray-200 bg-gray-50 px-2 py-0.5 text-xs text-gray-600">{m}</span>
            ))}
          </div>
        </div>
      )}
    </Section>
  )
}

// ── Contact card ──────────────────────────────────────────────────────────────
function ContactCard({ title, icon: Icon, name, phone, email, license }) {
  if (!name && !phone && !email) return (
    <div className="rounded-card bg-white shadow-card p-5">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="h-4 w-4 text-gray-400" /><p className="text-sm font-semibold text-gray-900">{title}</p>
      </div>
      <p className="text-sm text-gray-400">No information available</p>
    </div>
  )
  return (
    <div className="rounded-card bg-white shadow-card p-5">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="h-4 w-4 text-gray-400" /><p className="text-sm font-semibold text-gray-900">{title}</p>
      </div>
      <div className="space-y-2">
        {name && <p className="text-sm font-medium text-gray-900">{name}</p>}
        {phone && (
          <a href={`tel:${phone}`} className="flex items-center gap-2 text-sm text-secondary hover:text-primary-700">
            <Phone className="h-3.5 w-3.5" />{phone}
          </a>
        )}
        {email && (
          <a href={`mailto:${email}`} className="flex items-center gap-2 text-sm text-secondary hover:text-primary-700 truncate">
            <Mail className="h-3.5 w-3.5 shrink-0" />{email}
          </a>
        )}
        {license && <p className="flex items-center gap-1.5 text-xs text-gray-400"><CheckCircle2 className="h-3 w-3" />Lic: {license}</p>}
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function LeadDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [lead, setLead] = useState(null)
  const [similar, setSimilar] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setLoading(true); setError(null)
    getLead(id).then(data => {
      if (data.error) { setError(data.error); return }
      setLead(data)
      if (data.trade) {
        getLeads({ trade: data.trade, limit: 4 }).catch(() => ({ data: [] })).then(env => {
          const list = Array.isArray(env) ? env : (env.data || [])
          setSimilar(list.filter(l => l.id !== id).slice(0, 3))
        })
      }
    }).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  const handleSave = async () => {
    let email = localStorage.getItem('pipeline_email')
    if (!email) {
      email = window.prompt('Enter your email to save this lead:')
      if (!email) return
      localStorage.setItem('pipeline_email', email.trim())
    }
    const res = await fetch(`/api/pipeline/leads/${id}/save`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_email: email }),
    })
    if (res.ok) { setSaved(true); toast.success('Saved to pipeline') }
  }

  if (loading) return (
    <div className="space-y-5 animate-pulse">
      <div className="h-5 w-32 bg-gray-100 rounded" />
      <div className="rounded-card bg-white shadow-card p-6 space-y-3">
        <div className="h-6 w-2/3 bg-gray-100 rounded" />
        <div className="h-4 w-1/2 bg-gray-100 rounded" />
        <div className="h-8 w-24 bg-gray-100 rounded" />
      </div>
      <div className="grid grid-cols-3 gap-5">
        <div className="col-span-2 h-48 rounded-card bg-gray-100" />
        <div className="h-48 rounded-card bg-gray-100" />
      </div>
    </div>
  )

  if (error || !lead) return (
    <div className="flex flex-col items-center py-16">
      <p className="font-semibold text-gray-700 mb-1">{error === 'Lead not found' ? 'Lead not found' : 'Error loading lead'}</p>
      <p className="text-sm text-gray-400 mb-5">{error}</p>
      <div className="flex gap-3">
        <button onClick={() => navigate(-1)} className="btn btn-secondary">Go back</button>
        <Link to="/leads" className="btn btn-primary">Browse leads</Link>
      </div>
    </div>
  )

  const owner = lead.owner || {}
  const gc = lead.gc || {}

  return (
    <div className="space-y-5 max-w-5xl">
      {/* Breadcrumb */}
      <Link to="/leads" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Leads
      </Link>

      {/* Hero */}
      <div className="rounded-card bg-white shadow-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-start gap-5">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={clsx('inline-flex items-center rounded px-2 py-0.5 text-xs font-medium', TRADE_BADGE[lead.trade] ?? 'bg-gray-100 text-gray-600')}>
                {lead.trade}
              </span>
              <span className="inline-flex items-center rounded px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 capitalize">
                {lead.type || 'permit'}
              </span>
              {lead.deadline && (
                <span className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium bg-red-50 text-red-600 border border-red-100">
                  <Calendar className="h-3 w-3" /> Due {relDate(lead.deadline)}
                </span>
              )}
            </div>
            <h1 className="text-lg font-bold text-gray-900 leading-snug">{lead.title}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-gray-400">
              {lead.addr && <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{lead.addr}</span>}
              {lead.posted && <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" />{relDate(lead.posted)} · {fmtDate(lead.posted)}</span>}
            </div>
          </div>
          <div className="flex items-center gap-5 shrink-0">
            <ScoreGauge score={lead.score || 0} />
            <div className="text-right">
              <p className="text-2xl font-black text-gray-900">{fmtVal(lead.value)}</p>
              <p className="text-xs text-gray-400 mt-0.5">Est. project value</p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-5 flex flex-wrap gap-2 pt-4 border-t border-gray-100">
          <button onClick={handleSave} disabled={saved}
            className={clsx('btn btn-sm flex items-center gap-1.5', saved ? 'btn-secondary text-rose-500 border-rose-200' : 'btn-primary')}>
            <Heart className={clsx('h-3.5 w-3.5', saved && 'fill-rose-500')} />
            {saved ? 'Saved' : 'Save to Pipeline'}
          </button>
          {(owner.p || gc.p) && (
            <a href={`tel:${owner.p || gc.p}`} className="btn btn-secondary btn-sm flex items-center gap-1.5">
              <Phone className="h-3.5 w-3.5" /> Call
            </a>
          )}
          {(owner.e || gc.e) && (
            <a href={`mailto:${owner.e || gc.e}`} className="btn btn-secondary btn-sm flex items-center gap-1.5">
              <Mail className="h-3.5 w-3.5" /> Email
            </a>
          )}
          <Link to={`/alerts?trade=${lead.trade}`} className="btn btn-secondary btn-sm flex items-center gap-1.5">
            <Bell className="h-3.5 w-3.5" /> Alert for similar
          </Link>
        </div>
      </div>

      {/* 2-col layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left — main content */}
        <div className="lg:col-span-2 space-y-4">
          {lead.ai && <AIPanel ai={lead.ai} />}

          <Section title="Project Details" icon={Building2}>
            <DetailRow label="Source" value={lead.src} />
            <DetailRow label="Status" value={lead.status} />
            <DetailRow label="Permit Type" value={lead.permit_type} />
            <DetailRow label="Work Class" value={lead.work_class} />
            <DetailRow label="Posted" value={fmtDate(lead.posted)} />
            <DetailRow label="Deadline" value={lead.deadline ? `${fmtDate(lead.deadline)} (${relDate(lead.deadline)})` : null} accent />
            {lead.keywords?.length > 0 && (
              <div className="pt-3">
                <p className="text-xs text-gray-400 mb-2 flex items-center gap-1"><Tag className="h-3 w-3" />Keywords</p>
                <div className="flex flex-wrap gap-1.5">
                  {lead.keywords.slice(0, 14).map(k => (
                    <span key={k} className="rounded-md border border-gray-100 bg-gray-50 px-2 py-0.5 text-xs text-gray-500">{k}</span>
                  ))}
                </div>
              </div>
            )}
          </Section>

          {similar.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-900">Similar {lead.trade} Leads</h2>
                <Link to={`/leads?trade=${lead.trade}`} className="text-xs text-secondary hover:underline flex items-center gap-0.5">
                  View all <ChevronRight className="h-3 w-3" />
                </Link>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {similar.map(sl => <LeadCard key={sl.id} lead={sl} compact />)}
              </div>
            </div>
          )}
        </div>

        {/* Right — contacts + score */}
        <div className="space-y-4">
          <ContactCard title="Property Owner" icon={User} name={owner.n} phone={owner.p} email={owner.e} />
          <ContactCard title="General Contractor" icon={Building2} name={gc.n} phone={gc.p} email={gc.e} license={gc.lic} />

          <Section title="Score Breakdown" icon={Zap}>
            {[
              { label: 'Value Signal', score: Math.min(Math.round((lead.score || 0) * 0.28), 25), max: 25 },
              { label: 'Recency', score: Math.min(Math.round((lead.score || 0) * 0.27), 25), max: 25 },
              { label: 'Contact Quality', score: Math.min(Math.round((lead.score || 0) * 0.30), 30), max: 30 },
              { label: 'Market Fit', score: Math.min(Math.round((lead.score || 0) * 0.15), 20), max: 20 },
            ].map(({ label, score, max }) => (
              <div key={label} className="mb-2.5">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-500">{label}</span>
                  <span className="font-medium text-gray-700">{score}/{max}</span>
                </div>
                <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
                  <div className="h-full rounded-full bg-primary-500" style={{ width: `${(score/max)*100}%` }} />
                </div>
              </div>
            ))}
          </Section>

          <div className="rounded-card bg-white shadow-card p-4">
            <p className="text-xs text-gray-400 mb-2">Data Source</p>
            <div className="space-y-1 text-xs text-gray-500">
              <div className="flex justify-between"><span>Source ID</span><code className="text-gray-400">{lead.src || '—'}</code></div>
              <div className="flex justify-between"><span>Lead ID</span><code className="text-gray-400">{lead.id?.slice(0,12)}…</code></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
