import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';

const STATUSES = [
  { key: 'NEW',           label: 'New',            color: 'bg-gray-100 text-gray-700',    dot: 'bg-gray-400' },
  { key: 'CONTACTED',     label: 'Contacted',      color: 'bg-blue-100 text-blue-700',    dot: 'bg-blue-500' },
  { key: 'PROPOSAL_SENT', label: 'Proposal Sent',  color: 'bg-amber-100 text-amber-700',  dot: 'bg-amber-500' },
  { key: 'WON',           label: 'Won ✓',          color: 'bg-emerald-100 text-emerald-700', dot: 'bg-emerald-500' },
  { key: 'LOST',          label: 'Lost',           color: 'bg-red-100 text-red-700',      dot: 'bg-red-400' },
];

function formatValue(v) {
  if (!v) return '--';
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `$${Math.round(v / 1_000)}K`;
  return `$${v}`;
}

// ── Email gate ──────────────────────────────────────────────────────────────

function EmailGate({ onEmail }) {
  const [val, setVal] = useState('');
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] gap-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-primary-100 flex items-center justify-center">
        <svg className="w-8 h-8 text-primary-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0H3" />
        </svg>
      </div>
      <div>
        <h2 className="text-xl font-bold text-gray-900">Your Lead Pipeline</h2>
        <p className="mt-1 text-gray-500 max-w-sm">Enter your email to access your saved leads and track your pipeline.</p>
      </div>
      <div className="flex gap-2 w-full max-w-sm">
        <input
          type="email"
          placeholder="your@email.com"
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && val && onEmail(val.trim())}
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <button
          onClick={() => val && onEmail(val.trim())}
          className="btn-primary"
        >
          Open
        </button>
      </div>
    </div>
  );
}

// ── Note modal ──────────────────────────────────────────────────────────────

function NoteModal({ item, onClose, onSaved }) {
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!text.trim()) return;
    setSaving(true);
    await fetch(`/api/pipeline/leads/${encodeURIComponent(item.lead_id)}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_email: item.user_email, note: text.trim() }),
    });
    setSaving(false);
    onSaved();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h3 className="font-semibold text-gray-900 mb-1">Add Note</h3>
        <p className="text-sm text-gray-500 mb-3 truncate">{item.lead?.title || item.lead_id}</p>
        <textarea
          autoFocus
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          placeholder="Called, left voicemail. Call back Thursday..."
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
        />
        <div className="mt-3 flex justify-end gap-2">
          <button onClick={onClose} className="btn-secondary text-sm">Cancel</button>
          <button onClick={save} disabled={saving || !text.trim()} className="btn-primary text-sm">
            {saving ? 'Saving...' : 'Save Note'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Pipeline card ───────────────────────────────────────────────────────────

function PipelineCard({ item, onStatusChange, onNote, onRemove }) {
  const lead = item.lead;
  const notes = item.notes || [];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <Link
            to={`/leads/${item.lead_id}`}
            className="text-sm font-semibold text-gray-900 hover:text-primary-700 line-clamp-2"
          >
            {lead?.title || item.lead_id}
          </Link>
          {lead && (
            <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
              <span className="font-medium text-gray-700">{formatValue(lead.value)}</span>
              {lead.addr && <span className="truncate">· {lead.addr}</span>}
            </div>
          )}
        </div>
        <button
          onClick={() => onRemove(item)}
          title="Remove from pipeline"
          className="text-gray-300 hover:text-red-400 transition-colors flex-shrink-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Contact quick-actions */}
      {lead && (lead.owner?.p || lead.gc?.p) && (
        <a
          href={`tel:${lead.owner?.p || lead.gc?.p}`}
          className="mt-2 inline-flex items-center gap-1 text-xs text-primary-600 hover:text-primary-800"
        >
          📞 {lead.owner?.p || lead.gc?.p}
        </a>
      )}

      {/* Notes */}
      {notes.length > 0 && (
        <div className="mt-2 space-y-1">
          {notes.slice(-2).map((n, i) => (
            <p key={i} className="text-xs text-gray-500 bg-gray-50 rounded px-2 py-1">
              "{n.text}"
            </p>
          ))}
          {notes.length > 2 && (
            <p className="text-xs text-gray-400">{notes.length - 2} more notes</p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-3 flex items-center gap-2">
        <select
          value={item.status}
          onChange={(e) => onStatusChange(item, e.target.value)}
          className="flex-1 rounded-lg border border-gray-200 bg-gray-50 px-2 py-1 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-primary-500"
        >
          {STATUSES.map((s) => (
            <option key={s.key} value={s.key}>{s.label}</option>
          ))}
        </select>
        <button
          onClick={() => onNote(item)}
          className="text-xs text-gray-500 hover:text-primary-600 border border-gray-200 rounded-lg px-2 py-1 hover:border-primary-300 transition-colors"
        >
          + Note
        </button>
      </div>
    </div>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function Pipeline() {
  const [email, setEmail] = useState(() => localStorage.getItem('pipeline_email') || '');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [noteTarget, setNoteTarget] = useState(null);

  const fetchPipeline = useCallback(async (userEmail) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/pipeline?email=${encodeURIComponent(userEmail)}`);
      const data = await res.json();
      setItems(data);
    } catch (err) {
      console.error('Pipeline fetch failed', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (email) fetchPipeline(email);
  }, [email, fetchPipeline]);

  const handleEmail = (e) => {
    localStorage.setItem('pipeline_email', e);
    setEmail(e);
  };

  const handleStatusChange = async (item, newStatus) => {
    setItems((prev) =>
      prev.map((i) => (i.id === item.id ? { ...i, status: newStatus } : i))
    );
    await fetch(`/api/pipeline/leads/${encodeURIComponent(item.lead_id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_email: email, status: newStatus }),
    });
  };

  const handleRemove = async (item) => {
    setItems((prev) => prev.filter((i) => i.id !== item.id));
    await fetch(`/api/pipeline/leads/${encodeURIComponent(item.lead_id)}?email=${encodeURIComponent(email)}`, {
      method: 'DELETE',
    });
  };

  if (!email) return <EmailGate onEmail={handleEmail} />;

  const byStatus = Object.fromEntries(STATUSES.map((s) => [s.key, []]));
  items.forEach((item) => {
    const key = item.status || 'NEW';
    if (byStatus[key]) byStatus[key].push(item);
    else byStatus.NEW.push(item);
  });

  const total = items.length;
  const won = byStatus.WON?.length || 0;
  const totalValue = items.reduce((sum, i) => sum + (i.lead?.value || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Pipeline</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {email} · {total} leads · {formatValue(totalValue)} total value
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-xs text-gray-400">Win rate</p>
            <p className="text-lg font-bold text-emerald-600">
              {total > 0 ? Math.round((won / total) * 100) : 0}%
            </p>
          </div>
          <button
            onClick={() => { localStorage.removeItem('pipeline_email'); setEmail(''); }}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            Switch account
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-center py-12 text-gray-400">Loading pipeline...</div>
      )}

      {!loading && total === 0 && (
        <div className="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-300">
          <div className="text-4xl mb-3">📋</div>
          <h3 className="font-semibold text-gray-700">No leads in your pipeline yet</h3>
          <p className="text-sm text-gray-400 mt-1">
            Browse leads and click the ♥ button to save them here.
          </p>
          <Link to="/leads" className="btn-primary mt-4 inline-block">Browse Leads</Link>
        </div>
      )}

      {/* Kanban columns */}
      {!loading && total > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {STATUSES.map((s) => (
            <div key={s.key}>
              <div className="flex items-center gap-2 mb-3">
                <span className={`w-2 h-2 rounded-full ${s.dot}`} />
                <h3 className="text-sm font-semibold text-gray-700">{s.label}</h3>
                <span className="ml-auto text-xs text-gray-400 bg-gray-100 rounded-full px-2 py-0.5">
                  {byStatus[s.key].length}
                </span>
              </div>
              <div className="space-y-3">
                {byStatus[s.key].map((item) => (
                  <PipelineCard
                    key={item.id}
                    item={item}
                    onStatusChange={handleStatusChange}
                    onNote={setNoteTarget}
                    onRemove={handleRemove}
                  />
                ))}
                {byStatus[s.key].length === 0 && (
                  <div className="rounded-xl border border-dashed border-gray-200 p-4 text-center text-xs text-gray-300">
                    None
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {noteTarget && (
        <NoteModal
          item={noteTarget}
          onClose={() => setNoteTarget(null)}
          onSaved={() => fetchPipeline(email)}
        />
      )}
    </div>
  );
}
