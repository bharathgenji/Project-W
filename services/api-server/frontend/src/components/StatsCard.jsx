import React from 'react';

export default function StatsCard({ title, value, change, changeLabel, icon, color = 'primary' }) {
  const colorMap = {
    primary: {
      bg: 'bg-primary-50',
      icon: 'text-primary-600',
      ring: 'ring-primary-200',
    },
    green: {
      bg: 'bg-emerald-50',
      icon: 'text-emerald-600',
      ring: 'ring-emerald-200',
    },
    blue: {
      bg: 'bg-blue-50',
      icon: 'text-blue-600',
      ring: 'ring-blue-200',
    },
    amber: {
      bg: 'bg-amber-50',
      icon: 'text-amber-600',
      ring: 'ring-amber-200',
    },
    rose: {
      bg: 'bg-rose-50',
      icon: 'text-rose-600',
      ring: 'ring-rose-200',
    },
  };

  const colors = colorMap[color] || colorMap.primary;

  const isPositive = change > 0;
  const isNegative = change < 0;

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-500 truncate">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900 tracking-tight">{value}</p>
          {(change !== undefined && change !== null) && (
            <div className="mt-2 flex items-center gap-1.5">
              {isPositive && (
                <span className="inline-flex items-center gap-0.5 text-sm font-medium text-emerald-600">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                  </svg>
                  +{change}%
                </span>
              )}
              {isNegative && (
                <span className="inline-flex items-center gap-0.5 text-sm font-medium text-rose-600">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 4.5l15 15m0 0V8.25m0 11.25H8.25" />
                  </svg>
                  {change}%
                </span>
              )}
              {change === 0 && (
                <span className="text-sm font-medium text-gray-400">No change</span>
              )}
              {changeLabel && (
                <span className="text-sm text-gray-400">{changeLabel}</span>
              )}
            </div>
          )}
        </div>
        {icon && (
          <div className={`flex items-center justify-center w-12 h-12 rounded-xl ${colors.bg} ring-1 ${colors.ring}`}>
            <span className={colors.icon}>{icon}</span>
          </div>
        )}
      </div>
    </div>
  );
}
