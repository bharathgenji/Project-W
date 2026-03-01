import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getLead, getLeads } from '../api/client';
import LeadCard from '../components/LeadCard';

const TRADE_COLORS = {
  ELECTRICAL:'#f59e0b', PLUMBING:'#3b82f6', HVAC:'#06b6d4',
  ROOFING:'#f97316', CONCRETE:'#6b7280', GENERAL:'#8b5cf6', DEFAULT:'#1d4ed8',
};
const TRADE_EMOJI = { ELECTRICAL:'⚡', PLUMBING:'🔧', HVAC:'❄️', ROOFING:'🏠', CONCRETE:'🏗️', GENERAL:'🔨', DEFAULT:'📋' };

function fmt(v) {
  if (!v && v !== 0) return '--';
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${Math.round(v/1e3)}K`;
  return `$${Number(v).toLocaleString()}`;
}
function fmtDate(s) {
  if (!s) return '--';
  try { return new Date(s).toLocaleDateString('en-US', { weekday:'long', year:'numeric', month:'long', day:'numeric' }); }
  catch { return s; }
}
function relDate(s) {
  if (!s) return null;
  const days = Math.floor((Date.now() - new Date(s).getTime()) / 86400000);
  if (days === 0) return 'Today'; if (days === 1) return 'Yesterday';
  if (days < 7) return `${days} days ago`; if (days < 30) return `${Math.floor(days/7)} weeks ago`;
  return `${Math.floor(days/30)} months ago`;
}

function ScoreRing({ score }) {
  const color = score >= 80 ? '#10b981' : score >= 60 ? '#3b82f6' : score >= 40 ? '#f59e0b' : '#9ca3af';
  const label = score >= 80 ? 'Hot 🔥' : score >= 60 ? 'Warm' : score >= 40 ? 'Fair' : 'Low';
  const r = 30, circ = 2 * Math.PI * r, dash = (score / 100) * circ;
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="80" height="80" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#f3f4f6" strokeWidth="8"/>
        <circle cx="40" cy="40" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={`${dash} ${circ - dash}`} strokeLinecap="round"
          transform="rotate(-90 40 40)" style={{transition:'stroke-dasharray 1s ease'}}/>
        <text x="40" y="44" textAnchor="middle" fontSize="18" fontWeight="700" fill={color}>{score}</text>
      </svg>
      <span className="text-xs font-semibold" style={{color}}>{label}</span>
    </div>
  );
}

// ── AI Enrichment Panel ──────────────────────────────────────────────────────
const PROJECT_TYPE_LABELS = {
  new_build: { label: 'New Construction', color: 'bg-emerald-100 text-emerald-800', icon: '🏗️' },
  renovation: { label: 'Renovation', color: 'bg-blue-100 text-blue-800', icon: '🔨' },
  repair: { label: 'Repair', color: 'bg-amber-100 text-amber-800', icon: '🔧' },
  addition: { label: 'Addition', color: 'bg-purple-100 text-purple-800', icon: '➕' },
  compliance: { label: 'Compliance', color: 'bg-gray-100 text-gray-800', icon: '📋' },
};
const OWNER_TYPE_LABELS = {
  residential: { label: 'Residential', color: 'bg-sky-100 text-sky-800', icon: '🏘️' },
  small_commercial: { label: 'Small Commercial', color: 'bg-indigo-100 text-indigo-800', icon: '🏪' },
  large_commercial: { label: 'Large Commercial', color: 'bg-violet-100 text-violet-800', icon: '🏢' },
  institutional: { label: 'Institutional / Gov', color: 'bg-rose-100 text-rose-800', icon: '🏛️' },
  industrial: { label: 'Industrial', color: 'bg-orange-100 text-orange-800', icon: '🏭' },
};

function AIEnrichmentPanel({ ai }) {
  if (!ai) return null;
  const pt = PROJECT_TYPE_LABELS[ai.project_type] || { label: ai.project_type, color: 'bg-gray-100 text-gray-700', icon: '📋' };
  const ot = OWNER_TYPE_LABELS[ai.owner_type] || { label: ai.owner_type, color: 'bg-gray-100 text-gray-700', icon: '👤' };
  return (
    <div className="card p-5 border-purple-200 bg-gradient-to-br from-white to-purple-50">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-6 h-6 rounded-md bg-purple-600 flex items-center justify-center">
          <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-gray-900">AI Analysis</h3>
        <span className="ml-auto text-[10px] font-medium text-purple-600 bg-purple-100 rounded-full px-2 py-0.5">Powered by Claude</span>
      </div>
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">Project Type</p>
          <span className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-semibold ${pt.color}`}>
            {pt.icon} {pt.label}
          </span>
        </div>
        <div>
          <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">Owner Type</p>
          <span className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-semibold ${ot.color}`}>
            {ot.icon} {ot.label}
          </span>
        </div>
        {ai.sqft && (
          <div>
            <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">Square Footage</p>
            <p className="text-sm font-bold text-gray-900">{ai.sqft.toLocaleString()} sqft</p>
          </div>
        )}
        {ai.units && (
          <div>
            <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">Units</p>
            <p className="text-sm font-bold text-gray-900">{ai.units} units</p>
          </div>
        )}
      </div>
      {ai.key_materials?.length > 0 && (
        <div>
          <p className="text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-2">Key Materials</p>
          <div className="flex flex-wrap gap-1.5">
            {ai.key_materials.map((m, i) => (
              <span key={i} className="rounded-md bg-white border border-gray-200 px-2 py-0.5 text-xs text-gray-700 shadow-sm">{m}</span>
            ))}
          </div>
        </div>
      )}
      {(ai.urgency || ai.complexity) && (
        <div className="mt-3 pt-3 border-t border-purple-100 flex gap-4">
          {ai.urgency && <div className="text-xs"><span className="text-gray-400">Urgency: </span>
            <span className={`font-semibold ${ai.urgency === 'high' ? 'text-red-600' : ai.urgency === 'medium' ? 'text-amber-600' : 'text-gray-600'}`}>{ai.urgency}</span></div>}
          {ai.complexity && <div className="text-xs"><span className="text-gray-400">Complexity: </span>
            <span className="font-semibold text-gray-700">{ai.complexity}</span></div>}
        </div>
      )}
    </div>
  );
}

// ── Contact Card ──────────────────────────────────────────────────────────────
function ContactCard({ title, icon, name, phone, email, license, children }) {
  if (!name && !children) return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">{icon} {title}</h3>
      <p className="text-sm text-gray-400">No information available</p>
    </div>
  );
  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">{icon} {title}</h3>
      {children || (
        <div className="space-y-2">
          {name && <p className="font-semibold text-gray-900">{name}</p>}
          {phone && (
            <a href={`tel:${phone}`} className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-800 font-medium group">
              <span className="w-7 h-7 rounded-lg bg-primary-50 flex items-center justify-center group-hover:bg-primary-100 transition-colors">📞</span>
              {phone}
            </a>
          )}
          {email && (
            <a href={`mailto:${email}`} className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-800 font-medium group">
              <span className="w-7 h-7 rounded-lg bg-primary-50 flex items-center justify-center group-hover:bg-primary-100 transition-colors">✉️</span>
              {email}
            </a>
          )}
          {license && <p className="text-xs text-gray-500 mt-1">🪪 License: {license}</p>}
        </div>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function LeadDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [lead, setLead] = useState(null);
  const [similarLeads, setSimilarLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function fetchData() {
      setLoading(true); setError(null);
      try {
        const data = await getLead(id);
        if (data.error) { setError(data.error); return; }
        setLead(data);
        if (data.trade) {
          const env = await getLeads({ trade: data.trade, limit: 6 }).catch(() => ({ data: [] }));
          const list = Array.isArray(env) ? env : (env.data || []);
          setSimilarLeads(list.filter(l => l.id !== id).slice(0, 3));
        }
      } catch (err) { setError(err.message); }
      finally { setLoading(false); }
    }
    fetchData();
  }, [id]);

  const handleSave = async () => {
    let email = localStorage.getItem('pipeline_email');
    if (!email) {
      email = window.prompt('Enter your email to save this lead:');
      if (!email) return;
      localStorage.setItem('pipeline_email', email.trim());
    }
    const res = await fetch(`/api/pipeline/leads/${id}/save`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_email: email }),
    });
    if (res.ok) setSaved(true);
  };

  if (loading) return (
    <div className="animate-pulse space-y-6">
      <div className="h-6 w-48 bg-gray-200 rounded"/>
      <div className="card p-6 space-y-4"><div className="h-7 w-2/3 bg-gray-200 rounded"/><div className="h-4 w-1/2 bg-gray-200 rounded"/></div>
      <div className="grid grid-cols-3 gap-6"><div className="col-span-2 h-64 bg-gray-200 rounded-xl"/><div className="h-64 bg-gray-200 rounded-xl"/></div>
    </div>
  );

  if (error || !lead) return (
    <div className="text-center py-16">
      <div className="text-5xl mb-4">🔍</div>
      <h3 className="text-lg font-semibold text-gray-900">{error === 'Lead not found' ? 'Lead Not Found' : 'Error'}</h3>
      <p className="text-gray-500 mt-1">{error}</p>
      <div className="mt-5 flex justify-center gap-3">
        <button onClick={() => navigate(-1)} className="btn-secondary">← Back</button>
        <Link to="/leads" className="btn-primary">Browse Leads</Link>
      </div>
    </div>
  );

  const score = lead.score || 0;
  const gc = lead.gc || {};
  const owner = lead.owner || {};
  const ai = lead.ai;
  const tradeColor = TRADE_COLORS[lead.trade] || TRADE_COLORS.DEFAULT;

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/leads" className="hover:text-gray-700">Leads</Link>
        <span>›</span>
        <span className="text-gray-900 font-medium truncate max-w-sm">{lead.trade} · {lead.type}</span>
      </nav>

      {/* Hero header */}
      <div className="card p-6 overflow-hidden relative">
        <div className="absolute top-0 right-0 w-64 h-64 rounded-full opacity-5" style={{background: tradeColor, transform: 'translate(30%, -30%)'}}/>
        <div className="flex flex-col sm:flex-row sm:items-start gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-sm font-semibold"
                style={{background: tradeColor + '18', color: tradeColor}}>
                {TRADE_EMOJI[lead.trade]||'📋'} {lead.trade}
              </span>
              <span className="rounded-lg bg-gray-100 px-2.5 py-1 text-sm font-medium text-gray-600 capitalize">{lead.type}</span>
              {lead.deadline && (
                <span className="rounded-lg bg-red-50 border border-red-200 px-2.5 py-1 text-sm font-medium text-red-700">
                  ⏰ Due {relDate(lead.deadline)}
                </span>
              )}
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 leading-snug">{lead.title}</h1>
            <div className="mt-3 flex items-center gap-4 flex-wrap text-sm text-gray-500">
              <span>📍 {lead.addr || '--'}</span>
              <span>🕐 {relDate(lead.posted)} · {fmtDate(lead.posted)}</span>
            </div>
          </div>
          <div className="flex items-center gap-4 flex-shrink-0">
            <ScoreRing score={score} />
            <div className="text-right">
              <p className="text-3xl font-black text-gray-900">{fmt(lead.value)}</p>
              <p className="text-xs text-gray-500 mt-0.5">Est. Project Value</p>
            </div>
          </div>
        </div>
        {/* Action buttons */}
        <div className="mt-5 flex flex-wrap gap-2 pt-5 border-t border-gray-100">
          <button onClick={handleSave} disabled={saved}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-all ${saved ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'btn-primary'}`}>
            {saved ? '❤️ Saved to Pipeline' : '🤍 Save to Pipeline'}
          </button>
          {(owner.p || gc.p) && (
            <a href={`tel:${owner.p || gc.p}`} className="flex items-center gap-2 btn-secondary text-sm">
              📞 Call Now
            </a>
          )}
          {(owner.e || gc.e) && (
            <a href={`mailto:${owner.e || gc.e}`} className="flex items-center gap-2 btn-secondary text-sm">
              ✉️ Email
            </a>
          )}
          <Link to={`/alerts?trade=${lead.trade}&state=${(lead.addr||'').split(',').slice(-2,-1)[0]?.trim()||''}`}
            className="flex items-center gap-2 btn-secondary text-sm">
            🔔 Set Alert for Similar
          </Link>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Details + Similar */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Enrichment */}
          {ai && <AIEnrichmentPanel ai={ai} />}

          {/* Project details */}
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-4">📄 Project Details</h2>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-xs text-gray-400 uppercase tracking-wider mb-1">Type</dt>
                <dd className="text-sm font-semibold text-gray-900 capitalize">{lead.type || '--'}</dd>
              </div>
              <div>
                <dt className="text-xs text-gray-400 uppercase tracking-wider mb-1">Source</dt>
                <dd className="text-sm font-semibold text-gray-900">{lead.src || '--'}</dd>
              </div>
              {lead.deadline && (
                <div className="col-span-2">
                  <dt className="text-xs text-gray-400 uppercase tracking-wider mb-1">Submission Deadline</dt>
                  <dd className="text-sm font-bold text-red-600">{fmtDate(lead.deadline)} ({relDate(lead.deadline)})</dd>
                </div>
              )}
              {lead.keywords?.length > 0 && (
                <div className="col-span-2">
                  <dt className="text-xs text-gray-400 uppercase tracking-wider mb-2">Keywords</dt>
                  <dd className="flex flex-wrap gap-1.5">
                    {lead.keywords.slice(0, 12).map(k => (
                      <span key={k} className="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600">{k}</span>
                    ))}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Similar Leads */}
          {similarLeads.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-gray-900">Similar {lead.trade} Leads</h2>
                <Link to={`/leads?trade=${lead.trade}`} className="text-xs text-primary-600 hover:underline">View all →</Link>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {similarLeads.map(sl => <LeadCard key={sl.id} lead={sl} compact />)}
              </div>
            </div>
          )}
        </div>

        {/* Right: Contacts + Score */}
        <div className="space-y-4">
          {/* Owner */}
          <ContactCard title="Property Owner" icon="👤" name={owner.n} phone={owner.p} email={owner.e} />

          {/* GC */}
          <ContactCard title="General Contractor" icon="🏗️" name={gc.n} phone={gc.p} email={gc.e} license={gc.lic} />

          {/* Score breakdown */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">📊 Score Breakdown</h3>
            {[
              { label: 'Value Signal', val: Math.min(score >= 80 ? 25 : Math.round(score * 0.28), 25), max: 25 },
              { label: 'Recency', val: Math.min(score >= 80 ? 25 : Math.round(score * 0.27), 25), max: 25 },
              { label: 'Contact Quality', val: Math.min(score >= 80 ? 30 : Math.round(score * 0.30), 30), max: 30 },
              { label: 'Market Fit', val: Math.min(score >= 80 ? 20 : Math.round(score * 0.15), 20), max: 20 },
            ].map(({ label, val, max }) => (
              <div key={label} className="mb-3">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-600">{label}</span>
                  <span className="font-semibold text-gray-800">{val}/{max}</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-primary-500 transition-all" style={{width:`${(val/max)*100}%`}}/>
                </div>
              </div>
            ))}
          </div>

          {/* Source metadata */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">🔗 Data Source</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Source ID</span><span className="font-mono text-xs text-gray-700">{lead.src || '--'}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Lead ID</span><span className="font-mono text-xs text-gray-400 truncate ml-2">{lead.id?.slice(0,12)}…</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Posted</span><span className="text-gray-700">{relDate(lead.posted)}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Updated</span><span className="text-gray-700">{relDate(lead.updated)}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
