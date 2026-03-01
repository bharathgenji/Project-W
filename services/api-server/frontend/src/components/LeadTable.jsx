import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const columns = [
  { key: 'score', label: 'Score', sortable: true },
  { key: 'title', label: 'Title', sortable: false },
  { key: 'trade', label: 'Trade', sortable: true },
  { key: 'value', label: 'Value', sortable: true },
  { key: 'addr', label: 'Location', sortable: false },
  { key: 'posted', label: 'Posted', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
];

function formatCurrency(value) {
  if (!value && value !== 0) return '--';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr) {
  if (!dateStr) return '--';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

function getScoreColor(score) {
  if (score >= 80) return 'bg-emerald-100 text-emerald-700 ring-emerald-600/20';
  if (score >= 60) return 'bg-blue-100 text-blue-700 ring-blue-600/20';
  if (score >= 40) return 'bg-amber-100 text-amber-700 ring-amber-600/20';
  return 'bg-gray-100 text-gray-700 ring-gray-600/20';
}

function getStatusBadge(status) {
  const statusMap = {
    new: 'bg-blue-50 text-blue-700 ring-blue-600/20',
    active: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
    closed: 'bg-gray-100 text-gray-600 ring-gray-500/20',
    awarded: 'bg-purple-50 text-purple-700 ring-purple-600/20',
  };
  const normalized = (status || 'new').toLowerCase();
  return statusMap[normalized] || statusMap.new;
}

const tradeColors = {
  ELECTRICAL: 'bg-yellow-50 text-yellow-700',
  PLUMBING: 'bg-blue-50 text-blue-700',
  HVAC: 'bg-cyan-50 text-cyan-700',
  ROOFING: 'bg-orange-50 text-orange-700',
  CONCRETE: 'bg-gray-100 text-gray-700',
  GENERAL: 'bg-primary-50 text-primary-700',
  MECHANICAL: 'bg-rose-50 text-rose-700',
  FIRE: 'bg-red-50 text-red-700',
};

export default function LeadTable({ leads = [], loading = false }) {
  const navigate = useNavigate();
  const [sortKey, setSortKey] = useState('score');
  const [sortDir, setSortDir] = useState('desc');

  const handleSort = (key) => {
    if (key === sortKey) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sortedLeads = [...leads].sort((a, b) => {
    let aVal = a[sortKey];
    let bVal = b[sortKey];

    if (sortKey === 'value') {
      aVal = aVal || 0;
      bVal = bVal || 0;
    }
    if (sortKey === 'score') {
      aVal = aVal || 0;
      bVal = bVal || 0;
    }
    if (sortKey === 'posted') {
      aVal = aVal || '';
      bVal = bVal || '';
    }

    if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  if (loading) {
    return (
      <div className="card overflow-hidden">
        <div className="animate-pulse">
          <div className="h-12 bg-gray-100" />
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-6 py-4 border-t border-gray-100">
              <div className="h-4 w-12 bg-gray-200 rounded" />
              <div className="h-4 w-48 bg-gray-200 rounded" />
              <div className="h-4 w-20 bg-gray-200 rounded" />
              <div className="h-4 w-24 bg-gray-200 rounded" />
              <div className="h-4 w-32 bg-gray-200 rounded" />
              <div className="h-4 w-20 bg-gray-200 rounded" />
              <div className="h-4 w-16 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (leads.length === 0) {
    return (
      <div className="card p-12 text-center">
        <svg className="mx-auto w-12 h-12 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12H9.75m3 0h3m-3 0H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
        <h3 className="mt-3 text-sm font-semibold text-gray-900">No leads found</h3>
        <p className="mt-1 text-sm text-gray-500">Try adjusting your filters or search criteria.</p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider ${
                    col.sortable ? 'cursor-pointer hover:text-gray-700 select-none' : ''
                  }`}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortKey === col.key && (
                      <svg className={`w-3.5 h-3.5 transition-transform ${sortDir === 'asc' ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                      </svg>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {sortedLeads.map((lead) => (
              <tr
                key={lead.id}
                onClick={() => navigate(`/leads/${lead.id}`)}
                className="hover:bg-primary-50/50 cursor-pointer transition-colors duration-100"
              >
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`inline-flex items-center justify-center w-10 h-6 rounded-full text-xs font-bold ring-1 ring-inset ${getScoreColor(lead.score)}`}>
                    {lead.score || 0}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="max-w-xs">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {lead.title || lead.desc?.slice(0, 80) || 'Untitled Lead'}
                    </p>
                    {lead.type && (
                      <p className="text-xs text-gray-400 mt-0.5 capitalize">{lead.type}</p>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${
                    tradeColors[lead.trade] || 'bg-gray-100 text-gray-700'
                  }`}>
                    {lead.trade || '--'}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                  {formatCurrency(lead.value)}
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm text-gray-600 truncate max-w-[200px]">{lead.addr || '--'}</p>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(lead.posted)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset capitalize ${getStatusBadge(lead.status)}`}>
                    {lead.status || 'new'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
