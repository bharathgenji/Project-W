import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts';

const CHART_COLORS = [
  '#4f46e5', // indigo
  '#0891b2', // cyan
  '#059669', // emerald
  '#d97706', // amber
  '#dc2626', // red
  '#7c3aed', // violet
  '#db2777', // pink
  '#2563eb', // blue
  '#ca8a04', // yellow
  '#16a34a', // green
];

function CustomTooltip({ active, payload, label, formatter }) {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg ring-1 ring-gray-200 px-4 py-3 text-sm">
      <p className="font-medium text-gray-900 mb-1">{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-gray-600">{entry.name}:</span>
          <span className="font-semibold text-gray-900">
            {formatter ? formatter(entry.value) : entry.value.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function ChartWidget({
  type = 'bar',
  data = [],
  dataKey = 'value',
  nameKey = 'name',
  title,
  subtitle,
  height = 300,
  colors = CHART_COLORS,
  showGrid = true,
  showLegend = false,
  formatter,
  multiSeries,
  className = '',
}) {
  if (!data || data.length === 0) {
    return (
      <div className={`card p-6 ${className}`}>
        {title && <h3 className="text-sm font-semibold text-gray-900 mb-1">{title}</h3>}
        {subtitle && <p className="text-xs text-gray-500 mb-4">{subtitle}</p>}
        <div className="flex items-center justify-center text-gray-400 text-sm" style={{ height }}>
          No data available
        </div>
      </div>
    );
  }

  const renderChart = () => {
    if (type === 'line') {
      return (
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />}
            <XAxis
              dataKey={nameKey}
              tick={{ fontSize: 12, fill: '#6b7280' }}
              axisLine={{ stroke: '#e5e7eb' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: '#6b7280' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={formatter}
            />
            <Tooltip content={<CustomTooltip formatter={formatter} />} />
            {showLegend && <Legend />}
            {multiSeries ? (
              multiSeries.map((series, i) => (
                <Line
                  key={series.key}
                  type="monotone"
                  dataKey={series.key}
                  name={series.name || series.key}
                  stroke={colors[i % colors.length]}
                  strokeWidth={2}
                  dot={{ r: 4, fill: colors[i % colors.length] }}
                  activeDot={{ r: 6 }}
                />
              ))
            ) : (
              <Line
                type="monotone"
                dataKey={dataKey}
                stroke={colors[0]}
                strokeWidth={2}
                dot={{ r: 4, fill: colors[0] }}
                activeDot={{ r: 6 }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      );
    }

    // Bar chart (default)
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />}
          <XAxis
            dataKey={nameKey}
            tick={{ fontSize: 11, fill: '#6b7280' }}
            axisLine={{ stroke: '#e5e7eb' }}
            tickLine={false}
            interval={0}
            angle={data.length > 8 ? -30 : 0}
            textAnchor={data.length > 8 ? 'end' : 'middle'}
            height={data.length > 8 ? 60 : 30}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#6b7280' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={formatter}
          />
          <Tooltip content={<CustomTooltip formatter={formatter} />} />
          {showLegend && <Legend />}
          {multiSeries ? (
            multiSeries.map((series, i) => (
              <Bar
                key={series.key}
                dataKey={series.key}
                name={series.name || series.key}
                fill={colors[i % colors.length]}
                radius={[4, 4, 0, 0]}
              />
            ))
          ) : (
            <Bar dataKey={dataKey} radius={[4, 4, 0, 0]}>
              {data.map((_, index) => (
                <Cell key={index} fill={colors[index % colors.length]} />
              ))}
            </Bar>
          )}
        </BarChart>
      </ResponsiveContainer>
    );
  };

  return (
    <div className={`card p-6 ${className}`}>
      {(title || subtitle) && (
        <div className="mb-4">
          {title && <h3 className="text-sm font-semibold text-gray-900">{title}</h3>}
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      )}
      {renderChart()}
    </div>
  );
}
