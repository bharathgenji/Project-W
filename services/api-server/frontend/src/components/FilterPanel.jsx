import React from 'react';

const TRADES = [
  { value: '', label: 'All Trades' },
  { value: 'ELECTRICAL', label: 'Electrical' },
  { value: 'PLUMBING', label: 'Plumbing' },
  { value: 'HVAC', label: 'HVAC' },
  { value: 'ROOFING', label: 'Roofing' },
  { value: 'CONCRETE', label: 'Concrete' },
  { value: 'GENERAL', label: 'General' },
  { value: 'MECHANICAL', label: 'Mechanical' },
  { value: 'FIRE', label: 'Fire Protection' },
  { value: 'DEMOLITION', label: 'Demolition' },
  { value: 'PAINTING', label: 'Painting' },
  { value: 'FLOORING', label: 'Flooring' },
  { value: 'LANDSCAPING', label: 'Landscaping' },
  { value: 'SOLAR', label: 'Solar' },
  { value: 'STRUCTURAL', label: 'Structural' },
];

const US_STATES = [
  { value: '', label: 'All States' },
  { value: 'AL', label: 'Alabama' },
  { value: 'AK', label: 'Alaska' },
  { value: 'AZ', label: 'Arizona' },
  { value: 'AR', label: 'Arkansas' },
  { value: 'CA', label: 'California' },
  { value: 'CO', label: 'Colorado' },
  { value: 'CT', label: 'Connecticut' },
  { value: 'DE', label: 'Delaware' },
  { value: 'FL', label: 'Florida' },
  { value: 'GA', label: 'Georgia' },
  { value: 'HI', label: 'Hawaii' },
  { value: 'ID', label: 'Idaho' },
  { value: 'IL', label: 'Illinois' },
  { value: 'IN', label: 'Indiana' },
  { value: 'IA', label: 'Iowa' },
  { value: 'KS', label: 'Kansas' },
  { value: 'KY', label: 'Kentucky' },
  { value: 'LA', label: 'Louisiana' },
  { value: 'ME', label: 'Maine' },
  { value: 'MD', label: 'Maryland' },
  { value: 'MA', label: 'Massachusetts' },
  { value: 'MI', label: 'Michigan' },
  { value: 'MN', label: 'Minnesota' },
  { value: 'MS', label: 'Mississippi' },
  { value: 'MO', label: 'Missouri' },
  { value: 'MT', label: 'Montana' },
  { value: 'NE', label: 'Nebraska' },
  { value: 'NV', label: 'Nevada' },
  { value: 'NH', label: 'New Hampshire' },
  { value: 'NJ', label: 'New Jersey' },
  { value: 'NM', label: 'New Mexico' },
  { value: 'NY', label: 'New York' },
  { value: 'NC', label: 'North Carolina' },
  { value: 'ND', label: 'North Dakota' },
  { value: 'OH', label: 'Ohio' },
  { value: 'OK', label: 'Oklahoma' },
  { value: 'OR', label: 'Oregon' },
  { value: 'PA', label: 'Pennsylvania' },
  { value: 'RI', label: 'Rhode Island' },
  { value: 'SC', label: 'South Carolina' },
  { value: 'SD', label: 'South Dakota' },
  { value: 'TN', label: 'Tennessee' },
  { value: 'TX', label: 'Texas' },
  { value: 'UT', label: 'Utah' },
  { value: 'VT', label: 'Vermont' },
  { value: 'VA', label: 'Virginia' },
  { value: 'WA', label: 'Washington' },
  { value: 'WV', label: 'West Virginia' },
  { value: 'WI', label: 'Wisconsin' },
  { value: 'WY', label: 'Wyoming' },
];

const SORT_OPTIONS = [
  { value: 'score', label: 'Highest Score' },
  { value: 'value', label: 'Highest Value' },
  { value: 'date', label: 'Most Recent' },
];

export { TRADES, US_STATES, SORT_OPTIONS };

export default function FilterPanel({ filters, onChange, onReset, className = '' }) {
  const handleChange = (key, value) => {
    onChange({ ...filters, [key]: value });
  };

  const activeCount = Object.entries(filters).filter(
    ([key, val]) => val && key !== 'sort_by'
  ).length;

  return (
    <div className={`card p-5 ${className}`}>
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75" />
          </svg>
          <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
          {activeCount > 0 && (
            <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary-100 text-primary-700 text-xs font-bold">
              {activeCount}
            </span>
          )}
        </div>
        {activeCount > 0 && onReset && (
          <button
            onClick={onReset}
            className="text-xs font-medium text-primary-600 hover:text-primary-700"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="space-y-4">
        {/* Trade */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">Trade</label>
          <select
            value={filters.trade || ''}
            onChange={(e) => handleChange('trade', e.target.value)}
            className="select-field"
          >
            {TRADES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* State */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">State</label>
          <select
            value={filters.state || ''}
            onChange={(e) => handleChange('state', e.target.value)}
            className="select-field"
          >
            {US_STATES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        {/* Value Range */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">Value Range</label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              placeholder="Min"
              value={filters.min_value || ''}
              onChange={(e) => handleChange('min_value', e.target.value)}
              className="input-field"
            />
            <span className="text-gray-400 text-sm flex-shrink-0">to</span>
            <input
              type="number"
              placeholder="Max"
              value={filters.max_value || ''}
              onChange={(e) => handleChange('max_value', e.target.value)}
              className="input-field"
            />
          </div>
        </div>

        {/* Sort By */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">Sort By</label>
          <select
            value={filters.sort_by || 'score'}
            onChange={(e) => handleChange('sort_by', e.target.value)}
            className="select-field"
          >
            {SORT_OPTIONS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
