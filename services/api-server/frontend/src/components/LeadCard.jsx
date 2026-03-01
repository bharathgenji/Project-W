import React, { useState } from 'react';
import { Link } from 'react-router-dom';

// ── Formatting helpers ──────────────────────────────────────────────────────

function formatValue(value) {
  if (!value && value !== 0) return '--';
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${value.toLocaleString()}`;
}

function relativeDate(dateStr) {
  if (!dateStr) return null;
  try {
    const diff = Date.now() - new Date(dateStr).getTime();
    const days = Math.floor(diff / 86_400_000);
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days}d ago`;
    if (days < 30) return `${Math.floor(days / 7)}w ago`;
    if (days < 365) return `${Math.floor(days / 30)}mo ago`;
    return `${Math.floor(days / 365)}y ago`;
  } catch {
    return null;
  }
}

function getScoreStyle(score) {
  if (score >= 80) return { bg: 'bg-emerald-500', label: 'Hot 🔥' };
  if (score >= 60) return { bg: 'bg-blue-500', label: 'Warm' };
  if (score >= 40) return { bg: 'bg-amber-500', label: 'Fair' };
  return { bg: 'bg-gray-400', label: 'Low' };
}

const TRADE_COLORS = {
  ELECTRICAL: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  PLUMBING:   'bg-blue-100 text-blue-800 border-blue-200',
  HVAC:       'bg-cyan-100 text-cyan-800 border-cyan-200',
  ROOFING:    'bg-orange-100 text-orange-800 border-orange-200',
  CONCRETE:   'bg-stone-100 text-stone-800 border-stone-200',
  FRAMING:    'bg-lime-100 text-lime-800 border-lime-200',
  DRYWALL:    'bg-slate-100 text-slate-800 border-slate-200',
  PAINTING:   'bg-pink-100 text-pink-800 border-pink-200',
  GENERAL:    'bg-violet-100 text-violet-800 border-violet-200',
  DEFAULT:    'bg-gray-100 text-gray-700 border-gray-200',
};

// ── Save to pipeline helper ─────────────────────────────────────────────────

async function saveLeadToPipeline(leadId, email) {
  const res = await fetch(`/api/pipeline/leads/${encodeURIComponent(leadId)}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_email: email }),
  });
  return res.ok;
}

// ── Main component ──────────────────────────────────────────────────────────

export default function LeadCard({ lead, compact = false }) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const score = lead.score || 0;
  const trade = lead.trade || 'GENERAL';
  const scoreStyle = getScoreStyle(score);
  const tradeColor = TRADE_COLORS[trade] || TRADE_COLORS.DEFAULT;
  const phone = lead.owner?.p || lead.gc?.p || '';
  const posted = relativeDate(lead.posted);

  const handleSave = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    let email = localStorage.getItem('pipeline_email');
    if (!email) {
      email = window.prompt('Enter your email to save leads to your pipeline:');
      if (!email) return;
      localStorage.setItem('pipeline_email', email.trim());
    }
    setSaving(true);
    const ok = await saveLeadToPipeline(lead.id, email);
    setSaving(false);
    if (ok) setSaved(true);
  };

  return (
    <div className="card relative hover:shadow-md transition-all duration-200 group">
      {/* Save button (top-right) */}
      <button
        onClick={handleSave}
        disabled={saving || saved}
        title={saved ? 'Saved to pipeline' : 'Save to pipeline'}
        className={`absolute top-3 right-3 p-1.5 rounded-full transition-colors z-10 ${
          saved
            ? 'text-rose-500 bg-rose-50'
            : 'text-gray-300 hover:text-rose-400 hover:bg-rose-50'
        }`}
      >
        <svg className="w-4 h-4" fill={saved ? 'currentColor' : 'none'} viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
        </svg>
      </button>

      <Link to={`/leads/${lead.id}`} className="block p-5 pr-10">
        {/* Header row */}
        <div className="flex items-start gap-3">
          <div className={`flex-shrink-0 w-10 h-10 rounded-lg ${scoreStyle.bg} flex items-center justify-center text-white font-bold text-sm shadow-sm`}>
            {score}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-gray-900 group-hover:text-primary-700 line-clamp-2 transition-colors leading-snug">
              {lead.title || 'Untitled Lead'}
            </h3>
            <div className="mt-1.5 flex items-center gap-1.5 flex-wrap">
              <span className={`inline-block rounded border px-1.5 py-0.5 text-xs font-medium ${tradeColor}`}>
                {trade}
              </span>
              <span className="inline-block rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-500 capitalize">
                {lead.type || 'permit'}
              </span>
              {lead.deadline && (
                <span className="inline-block rounded bg-red-50 border border-red-200 px-1.5 py-0.5 text-xs font-medium text-red-700">
                  Due {relativeDate(lead.deadline)}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Value + address */}
        <div className={`mt-3 ${compact ? 'space-y-1' : 'space-y-2'}`}>
          <div className="flex items-center justify-between">
            <span className="text-base font-bold text-gray-900">{formatValue(lead.value)}</span>
            {posted && <span className="text-xs text-gray-400">{posted}</span>}
          </div>

          {lead.addr && (
            <p className="text-xs text-gray-500 truncate">
              📍 {lead.addr}
            </p>
          )}
        </div>

        {/* Contact row */}
        {!compact && (lead.owner?.n || lead.gc?.n || phone) && (
          <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between gap-2">
            <div className="min-w-0 flex-1">
              {lead.owner?.n && (
                <p className="text-xs text-gray-600 font-medium truncate">{lead.owner.n}</p>
              )}
              {lead.gc?.n && (
                <p className="text-xs text-gray-400 truncate">GC: {lead.gc.n}</p>
              )}
            </div>
            {phone && (
              <a
                href={`tel:${phone}`}
                onClick={(e) => e.stopPropagation()}
                className="flex-shrink-0 inline-flex items-center gap-1 rounded-lg bg-primary-50 hover:bg-primary-100 px-2.5 py-1.5 text-xs font-medium text-primary-700 transition-colors"
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 6.75z" />
                </svg>
                Call
              </a>
            )}
          </div>
        )}
      </Link>
    </div>
  );
}
