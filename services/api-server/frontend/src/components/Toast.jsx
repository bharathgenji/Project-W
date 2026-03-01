import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Toast – floating notification for real-time lead alerts.
 * Usage: <Toast message="..." leadId="..." onDismiss={fn} />
 */
export function Toast({ id, message, leadId, onDismiss }) {
  const navigate = useNavigate();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Animate in
    requestAnimationFrame(() => setVisible(true));
    // Auto-dismiss after 6 seconds
    const t = setTimeout(() => { setVisible(false); setTimeout(() => onDismiss(id), 300); }, 6000);
    return () => clearTimeout(t);
  }, [id, onDismiss]);

  return (
    <div
      className={`flex items-start gap-3 w-80 bg-white rounded-2xl shadow-xl border border-gray-200 p-4 transition-all duration-300 ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center">
        <svg className="w-4 h-4 text-primary-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-primary-700 mb-0.5">New Lead Match</p>
        <p className="text-sm text-gray-700 line-clamp-2">{message}</p>
        {leadId && (
          <button
            onClick={() => { navigate(`/leads/${leadId}`); onDismiss(id); }}
            className="mt-1.5 text-xs text-primary-600 font-medium hover:underline"
          >
            View lead →
          </button>
        )}
      </div>
      <button
        onClick={() => onDismiss(id)}
        className="flex-shrink-0 text-gray-300 hover:text-gray-500 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

/**
 * ToastContainer – renders a stack of toasts at bottom-right.
 * Parent passes toasts array and onDismiss handler.
 */
export function ToastContainer({ toasts, onDismiss }) {
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 sm:left-auto sm:translate-x-0 sm:right-6 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <Toast {...t} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  );
}
