import React, { useEffect, useState, useCallback } from 'react';
import { getMarket, getLeads } from '../api/client';
import { US_STATES } from '../components/FilterPanel';
import MapView from '../components/MapView';
import ChartWidget from '../components/ChartWidget';
import StatsCard from '../components/StatsCard';

function formatCurrency(value) {
  if (!value && value !== 0) return '--';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

// Approximate state center coordinates for map centering
const STATE_CENTERS = {
  AL: [32.806671, -86.791130],
  AK: [61.370716, -152.404419],
  AZ: [33.729759, -111.431221],
  AR: [34.969704, -92.373123],
  CA: [36.116203, -119.681564],
  CO: [39.059811, -105.311104],
  CT: [41.597782, -72.755371],
  DE: [39.318523, -75.507141],
  FL: [27.766279, -81.686783],
  GA: [33.040619, -83.643074],
  HI: [21.094318, -157.498337],
  ID: [44.240459, -114.478828],
  IL: [40.349457, -88.986137],
  IN: [39.849426, -86.258278],
  IA: [42.011539, -93.210526],
  KS: [38.526600, -96.726486],
  KY: [37.668140, -84.670067],
  LA: [31.169546, -91.867805],
  ME: [44.693947, -69.381927],
  MD: [39.063946, -76.802101],
  MA: [42.230171, -71.530106],
  MI: [43.326618, -84.536095],
  MN: [45.694454, -93.900192],
  MS: [32.741646, -89.678696],
  MO: [38.456085, -92.288368],
  MT: [46.921925, -110.454353],
  NE: [41.125370, -98.268082],
  NV: [38.313515, -117.055374],
  NH: [43.452492, -71.563896],
  NJ: [40.298904, -74.521011],
  NM: [34.840515, -106.248482],
  NY: [42.165726, -74.948051],
  NC: [35.630066, -79.806419],
  ND: [47.528912, -99.784012],
  OH: [40.388783, -82.764915],
  OK: [35.565342, -96.928917],
  OR: [44.572021, -122.070938],
  PA: [40.590752, -77.209755],
  RI: [41.680893, -71.511780],
  SC: [33.856892, -80.945007],
  SD: [44.299782, -99.438828],
  TN: [35.747845, -86.692345],
  TX: [31.054487, -97.563461],
  UT: [40.150032, -111.862434],
  VT: [44.045876, -72.710686],
  VA: [37.769337, -78.169968],
  WA: [47.400902, -121.490494],
  WV: [38.491226, -80.954456],
  WI: [44.268543, -89.616508],
  WY: [42.755966, -107.302490],
};

export default function MarketMaps() {
  const [selectedState, setSelectedState] = useState('CA');
  const [marketData, setMarketData] = useState(null);
  const [mapLeads, setMapLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMarketData = useCallback(async (state) => {
    setLoading(true);
    setError(null);
    try {
      const [market, leads] = await Promise.all([
        getMarket(state),
        getLeads({ state, limit: 50 }),
      ]);
      setMarketData(market);
      setMapLeads(leads);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedState) {
      fetchMarketData(selectedState);
    }
  }, [selectedState, fetchMarketData]);

  // Prepare map markers from leads
  const mapMarkers = mapLeads
    .filter((lead) => lead.lat && lead.lng)
    .map((lead) => ({
      id: lead.id,
      lat: Number(lead.lat),
      lng: Number(lead.lng),
      label: lead.title || lead.desc?.slice(0, 60) || 'Lead',
      sublabel: lead.trade,
      value: formatCurrency(lead.value),
    }));

  // Prepare trade chart data
  const tradeChartData = marketData?.trade_breakdown
    ? Object.entries(marketData.trade_breakdown).map(([name, value]) => ({
        name: name.charAt(0) + name.slice(1).toLowerCase(),
        value,
      }))
    : [];

  const stateCenter = STATE_CENTERS[selectedState] || [39.8283, -98.5795];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Market Intelligence</h2>
          <p className="text-sm text-gray-500 mt-0.5">Explore construction activity and market trends by state</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-gray-700">Select State:</label>
          <select
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="select-field w-52"
          >
            {US_STATES.filter((s) => s.value).map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Stats cards */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 animate-pulse">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card p-6">
              <div className="h-4 w-24 bg-gray-200 rounded" />
              <div className="mt-3 h-8 w-16 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      ) : marketData && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatsCard
            title="Total Leads"
            value={(marketData.total_leads || 0).toLocaleString()}
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            }
            color="primary"
          />
          <StatsCard
            title="Average Project Value"
            value={formatCurrency(marketData.avg_value || 0)}
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            color="green"
          />
          <StatsCard
            title="Active Contractors"
            value={(marketData.top_contractors?.length || 0).toLocaleString()}
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
              </svg>
            }
            color="blue"
          />
        </div>
      )}

      {/* Map */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">
          Lead Map - {US_STATES.find((s) => s.value === selectedState)?.label || selectedState}
          {mapMarkers.length > 0 && (
            <span className="ml-2 text-xs font-normal text-gray-400">
              ({mapMarkers.length} mapped leads)
            </span>
          )}
        </h3>
        {loading ? (
          <div className="h-96 bg-gray-100 rounded-xl animate-pulse" />
        ) : (
          <MapView
            markers={mapMarkers}
            center={stateCenter}
            zoom={mapMarkers.length > 0 ? 7 : 6}
            height="450px"
          />
        )}
      </div>

      {/* Bottom grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trade breakdown chart */}
        <ChartWidget
          type="bar"
          title="Trade Distribution"
          subtitle={`Construction activity breakdown in ${US_STATES.find((s) => s.value === selectedState)?.label || selectedState}`}
          data={tradeChartData}
          height={280}
        />

        {/* Top contractors */}
        <div className="card p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-1">Top Contractors</h3>
          <p className="text-xs text-gray-500 mb-4">Most active contractors in this market</p>
          {loading ? (
            <div className="animate-pulse space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-6 h-4 bg-gray-200 rounded" />
                  <div className="h-4 flex-1 bg-gray-200 rounded" />
                  <div className="w-12 h-4 bg-gray-200 rounded" />
                </div>
              ))}
            </div>
          ) : marketData?.top_contractors?.length > 0 ? (
            <div className="space-y-3">
              {marketData.top_contractors.slice(0, 10).map((contractor, index) => {
                const maxPermits = marketData.top_contractors[0].permits;
                const percentage = maxPermits > 0 ? (contractor.permits / maxPermits) * 100 : 0;
                return (
                  <div key={contractor.name} className="flex items-center gap-3">
                    <span className="text-xs font-medium text-gray-400 w-5 text-right">{index + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-900 truncate">{contractor.name}</span>
                        <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
                          {contractor.permits} permit{contractor.permits !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary-500 rounded-full transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-400 py-8 text-center">No contractor data for this market</p>
          )}
        </div>
      </div>
    </div>
  );
}
