import React from 'react';
import { Link } from 'react-router-dom';

function formatCurrency(value) {
  if (!value && value !== 0) return '--';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function getScoreColor(score) {
  if (score >= 80) return 'bg-emerald-500';
  if (score >= 60) return 'bg-blue-500';
  if (score >= 40) return 'bg-amber-500';
  return 'bg-gray-400';
}

function getScoreLabel(score) {
  if (score >= 80) return 'Hot';
  if (score >= 60) return 'Warm';
  if (score >= 40) return 'Moderate';
  return 'Low';
}

const tradeIcons = {
  ELECTRICAL: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
    </svg>
  ),
  PLUMBING: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  ),
  DEFAULT: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17l-5.25 3.5a.75.75 0 01-1.16-.63l.98-6.12L.84 6.7a.75.75 0 01.42-1.28l6.15-.89L10.14.37a.75.75 0 011.34 0l2.73 5.17 6.15.89a.75.75 0 01.42 1.28l-4.15 5.12.98 6.12a.75.75 0 01-1.16.63l-5.25-3.5z" />
    </svg>
  ),
};

const tradeTagColors = {
  ELECTRICAL: 'bg-yellow-100 text-yellow-800',
  PLUMBING: 'bg-blue-100 text-blue-800',
  HVAC: 'bg-cyan-100 text-cyan-800',
  ROOFING: 'bg-orange-100 text-orange-800',
  CONCRETE: 'bg-gray-100 text-gray-800',
  GENERAL: 'bg-primary-100 text-primary-800',
  MECHANICAL: 'bg-rose-100 text-rose-800',
  FIRE: 'bg-red-100 text-red-800',
};

export default function LeadCard({ lead }) {
  const score = lead.score || 0;
  const trade = lead.trade || 'GENERAL';

  return (
    <Link
      to={`/leads/${lead.id}`}
      className="card block p-5 hover:shadow-md hover:ring-primary-200 transition-all duration-200 group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 group-hover:text-primary-700 truncate transition-colors">
            {lead.title || lead.desc?.slice(0, 80) || 'Untitled Lead'}
          </h3>
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ${
              tradeTagColors[trade] || tradeTagColors.GENERAL
            }`}>
              {tradeIcons[trade] || tradeIcons.DEFAULT}
              {trade}
            </span>
            {lead.type && (
              <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 capitalize">
                {lead.type}
              </span>
            )}
          </div>
        </div>

        {/* Score badge */}
        <div className="flex flex-col items-center gap-1 flex-shrink-0">
          <div className={`flex items-center justify-center w-11 h-11 rounded-xl ${getScoreColor(score)} text-white font-bold text-lg shadow-sm`}>
            {score}
          </div>
          <span className="text-[10px] font-medium text-gray-400 uppercase tracking-wider">
            {getScoreLabel(score)}
          </span>
        </div>
      </div>

      {/* Value and address */}
      <div className="mt-4 space-y-2">
        <div className="flex items-center gap-2 text-sm">
          <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-semibold text-gray-900">{formatCurrency(lead.value)}</span>
        </div>
        {lead.addr && (
          <div className="flex items-start gap-2 text-sm text-gray-500">
            <svg className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
            </svg>
            <span className="truncate">{lead.addr}</span>
          </div>
        )}
      </div>

      {/* Footer */}
      {lead.posted && (
        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
          <span className="text-xs text-gray-400">
            {(() => {
              try {
                return new Date(lead.posted).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                });
              } catch {
                return lead.posted;
              }
            })()}
          </span>
          <span className="text-xs font-medium text-primary-600 group-hover:text-primary-700 transition-colors">
            View Details
          </span>
        </div>
      )}
    </Link>
  );
}
