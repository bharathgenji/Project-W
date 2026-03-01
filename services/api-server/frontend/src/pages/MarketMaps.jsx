import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { getLeads, getMarket } from '../api/client';
import ChartWidget from '../components/ChartWidget';
import StatsCard from '../components/StatsCard';

// ── Google Maps API loader ────────────────────────────────────────────────────

let mapsApiPromise = null;
function loadGoogleMaps(apiKey) {
  if (!mapsApiPromise) {
    mapsApiPromise = new Promise((resolve) => {
      if (window.google?.maps) { resolve(window.google.maps); return; }
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=marker`;
      script.async = true;
      script.defer = true;
      script.onload = () => resolve(window.google.maps);
      document.head.appendChild(script);
    });
  }
  return mapsApiPromise;
}

// ── Trade colours ─────────────────────────────────────────────────────────────
const TRADE_COLORS = {
  ELECTRICAL: '#f59e0b', PLUMBING: '#3b82f6', HVAC: '#06b6d4',
  ROOFING: '#f97316', CONCRETE: '#6b7280', GENERAL: '#8b5cf6',
  FRAMING: '#84cc16', DEFAULT: '#1d4ed8',
};
const TRADE_EMOJI = { ELECTRICAL:'⚡', PLUMBING:'🔧', HVAC:'❄️', ROOFING:'🏠', CONCRETE:'🏗️', GENERAL:'🔨', DEFAULT:'📋' };

function formatVal(v) {
  if (!v) return '--';
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${Math.round(v/1e3)}K`;
  return `$${v}`;
}

// ── City coordinates for leads without lat/lng ────────────────────────────────
const CITY_COORDS = {
  'Chicago': [41.8781, -87.6298], 'Houston': [29.7604, -95.3698], 'Austin': [30.2672, -97.7431],
  'Dallas': [32.7767, -96.7970], 'Nashville': [36.1627, -86.7816], 'Miami': [25.7617, -80.1918],
  'Los Angeles': [34.0522, -118.2437], 'Seattle': [47.6062, -122.3321], 'Phoenix': [33.4484, -112.0740],
  'Denver': [39.7392, -104.9903], 'Atlanta': [33.7490, -84.3880], 'Washington': [38.9072, -77.0369],
  'New York': [40.7128, -74.0060], 'Boston': [42.3601, -71.0589], 'San Francisco': [37.7749, -122.4194],
  'Portland': [45.5231, -122.6765], 'Charlotte': [35.2271, -80.8431], 'Indianapolis': [39.7684, -86.1581],
  'Louisville': [38.2527, -85.7585], 'Pittsburgh': [40.4406, -79.9959], 'St. Louis': [38.6270, -90.1994],
  'Orlando': [28.5383, -81.3792], 'Tampa': [27.9506, -82.4572], 'Minneapolis': [44.9778, -93.2650],
};

function getLeadCoords(lead) {
  if (lead.geo_lat && lead.geo_lng) return [lead.geo_lat, lead.geo_lng];
  const addr = lead.addr || '';
  for (const [city, coords] of Object.entries(CITY_COORDS)) {
    if (addr.includes(city)) return [coords[0] + (Math.random()-0.5)*0.08, coords[1] + (Math.random()-0.5)*0.08];
  }
  return null;
}

// ── Google Map component ──────────────────────────────────────────────────────
function GoogleMapView({ leads, apiKey, selectedLead, onSelect }) {
  const mapRef = React.useRef(null);
  const mapInstance = React.useRef(null);
  const markersRef = React.useRef([]);

  useEffect(() => {
    if (!mapRef.current || !apiKey) return;

    loadGoogleMaps(apiKey).then((maps) => {
      if (!mapInstance.current) {
        mapInstance.current = new maps.Map(mapRef.current, {
          center: { lat: 37.8, lng: -96 },
          zoom: 4,
          mapTypeId: 'roadmap',
          styles: [
            { featureType: 'poi', stylers: [{ visibility: 'off' }] },
            { featureType: 'transit', stylers: [{ visibility: 'off' }] },
          ],
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true,
        });
      }

      // Clear existing markers
      markersRef.current.forEach(m => m.setMap(null));
      markersRef.current = [];

      // Add markers for each lead
      leads.forEach(lead => {
        const coords = getLeadCoords(lead);
        if (!coords) return;
        const color = TRADE_COLORS[lead.trade] || TRADE_COLORS.DEFAULT;
        const isSelected = selectedLead?.id === lead.id;

        const marker = new maps.Marker({
          position: { lat: coords[0], lng: coords[1] },
          map: mapInstance.current,
          title: lead.title,
          icon: {
            path: maps.SymbolPath.CIRCLE,
            fillColor: color,
            fillOpacity: isSelected ? 1 : 0.75,
            strokeColor: 'white',
            strokeWeight: isSelected ? 3 : 2,
            scale: isSelected ? 14 : Math.min(10, Math.max(6, Math.log10((lead.value || 10000) + 1) * 3)),
          },
          zIndex: isSelected ? 1000 : lead.score || 50,
        });

        const infoWindow = new maps.InfoWindow({
          content: `
            <div style="font-family:-apple-system,sans-serif;max-width:280px;padding:4px">
              <div style="font-size:13px;font-weight:600;color:#111827;line-height:1.4">${lead.title?.slice(0,80) || ''}</div>
              <div style="margin-top:8px;display:flex;gap:8px;align-items:center">
                <span style="background:${color}22;color:${color};border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600">${lead.trade}</span>
                <span style="font-size:15px;font-weight:700;color:#111827">${formatVal(lead.value)}</span>
              </div>
              <div style="margin-top:6px;font-size:12px;color:#6b7280">📍 ${lead.addr || ''}</div>
              <a href="/leads/${lead.id}" style="display:inline-block;margin-top:10px;background:#1d4ed8;color:white;padding:6px 14px;border-radius:6px;font-size:12px;font-weight:600;text-decoration:none">View Lead →</a>
            </div>
          `,
        });

        marker.addListener('click', () => {
          onSelect(lead);
          infoWindow.open(mapInstance.current, marker);
        });

        markersRef.current.push(marker);
      });
    });
  }, [leads, apiKey, selectedLead]);

  if (!apiKey) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-100 rounded-xl">
        <div className="text-center p-8">
          <div className="text-4xl mb-3">🗺️</div>
          <p className="text-gray-500 font-medium">Map requires Google Maps API key</p>
          <p className="text-xs text-gray-400 mt-1">Add GOOGLE_MAPS_API_KEY to .env</p>
        </div>
      </div>
    );
  }

  return <div ref={mapRef} className="w-full h-full rounded-xl" />;
}

// ── States for filter ─────────────────────────────────────────────────────────
const STATES = ['TX','IL','FL','CA','NY','WA','AZ','CO','TN','GA','MO','NC','DC','IN','KY','PA'];

// ── Main page ─────────────────────────────────────────────────────────────────
export default function MarketMaps() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);
  const [selectedState, setSelectedState] = useState('');
  const [selectedTrade, setSelectedTrade] = useState('');
  const [marketData, setMarketData] = useState(null);
  const [mapsApiKey, setMapsApiKey] = useState('');

  // Get Google Maps API key from backend config
  useEffect(() => {
    fetch('/api/config').then(r => r.json()).then(cfg => {
      setMapsApiKey(cfg.google_maps_api_key || '');
    }).catch(() => {});
  }, []);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 100, sort_by: 'score' };
      if (selectedState) params.state = selectedState;
      if (selectedTrade) params.trade = selectedTrade;
      const env = await getLeads(params);
      const data = Array.isArray(env) ? env : (env.data || []);
      setLeads(data);
    } catch (err) {
      console.error('Failed to load leads for map', err);
    } finally {
      setLoading(false);
    }
  }, [selectedState, selectedTrade]);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);

  useEffect(() => {
    if (selectedState) {
      getMarket(selectedState).then(setMarketData).catch(() => {});
    } else {
      setMarketData(null);
    }
  }, [selectedState]);

  const tradeBreakdown = useMemo(() => {
    const counts = {};
    leads.forEach(l => { counts[l.trade] = (counts[l.trade] || 0) + 1; });
    return Object.entries(counts).sort((a,b) => b[1]-a[1]).map(([name, value]) => ({ name, value }));
  }, [leads]);

  const totalValue = useMemo(() => leads.reduce((s, l) => s + (l.value || 0), 0), [leads]);

  const tradeOptions = ['ELECTRICAL','PLUMBING','HVAC','ROOFING','CONCRETE','GENERAL'];

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <select value={selectedState} onChange={e => setSelectedState(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
          <option value="">All States</option>
          {STATES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={selectedTrade} onChange={e => setSelectedTrade(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
          <option value="">All Trades</option>
          {tradeOptions.map(t => <option key={t} value={t}>{TRADE_EMOJI[t]} {t}</option>)}
        </select>
        <div className="ml-auto text-sm text-gray-500">
          {loading ? 'Loading...' : `${leads.length} leads · ${formatVal(totalValue)} total value`}
        </div>
      </div>

      {/* Map + Stats row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2 h-[500px] rounded-xl overflow-hidden shadow-sm border border-gray-200">
          <GoogleMapView
            leads={leads}
            apiKey={mapsApiKey}
            selectedLead={selectedLead}
            onSelect={setSelectedLead}
          />
        </div>

        {/* Stats sidebar */}
        <div className="space-y-4">
          {/* Selected lead card */}
          {selectedLead ? (
            <div className="card p-4 border-primary-200 ring-1 ring-primary-100">
              <div className="flex items-start justify-between mb-2">
                <span className={`text-xs font-semibold rounded-full px-2 py-0.5`}
                  style={{background: (TRADE_COLORS[selectedLead.trade]||'#1d4ed8')+'22', color: TRADE_COLORS[selectedLead.trade]||'#1d4ed8'}}>
                  {TRADE_EMOJI[selectedLead.trade]||'📋'} {selectedLead.trade}
                </span>
                <button onClick={() => setSelectedLead(null)} className="text-gray-300 hover:text-gray-500">✕</button>
              </div>
              <p className="text-sm font-semibold text-gray-900 line-clamp-3">{selectedLead.title}</p>
              <p className="text-xl font-bold text-gray-900 mt-2">{formatVal(selectedLead.value)}</p>
              <p className="text-xs text-gray-500 mt-1">📍 {selectedLead.addr}</p>
              <Link to={`/leads/${selectedLead.id}`} className="mt-3 btn-primary text-xs block text-center">View Full Lead →</Link>
            </div>
          ) : (
            <div className="card p-4 text-center text-sm text-gray-400">
              <div className="text-2xl mb-1">📍</div>
              Click any marker to see lead details
            </div>
          )}

          {/* Trade breakdown */}
          {tradeBreakdown.length > 0 && (
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Trade Breakdown</h3>
              <div className="space-y-2">
                {tradeBreakdown.slice(0, 6).map(({ name, value }) => {
                  const pct = Math.round((value / leads.length) * 100);
                  return (
                    <div key={name}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="font-medium text-gray-700">{TRADE_EMOJI[name]||'📋'} {name}</span>
                        <span className="text-gray-500">{value} leads ({pct}%)</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{width:`${pct}%`, background: TRADE_COLORS[name]||'#1d4ed8'}} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Market stats */}
          {marketData && selectedState && (
            <div className="card p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">📊 {selectedState} Market</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-gray-500">Total Leads</span><span className="font-semibold">{marketData.total_leads}</span></div>
                <div className="flex justify-between"><span className="text-gray-500">Avg Value</span><span className="font-semibold">{formatVal(marketData.avg_value)}</span></div>
                {marketData.top_contractors?.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Top Contractors</p>
                    {marketData.top_contractors.slice(0,3).map(c => (
                      <div key={c.name} className="flex justify-between text-xs py-1 border-b border-gray-100">
                        <span className="text-gray-700 truncate">{c.name}</span>
                        <span className="text-gray-500 ml-2">{c.permits} permits</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Lead list below map */}
      <div>
        <h3 className="text-base font-semibold text-gray-900 mb-3">
          {selectedState || selectedTrade ? `Filtered Leads (${leads.length})` : `All Leads on Map (${leads.length})`}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {leads.slice(0, 9).map(lead => (
            <Link key={lead.id} to={`/leads/${lead.id}`}
              className={`card p-3 hover:shadow-md transition-all cursor-pointer ${selectedLead?.id === lead.id ? 'ring-2 ring-primary-500' : ''}`}
              onClick={() => setSelectedLead(lead)}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium rounded px-1.5 py-0.5"
                  style={{background: (TRADE_COLORS[lead.trade]||'#1d4ed8')+'18', color: TRADE_COLORS[lead.trade]||'#1d4ed8'}}>
                  {TRADE_EMOJI[lead.trade]||'📋'} {lead.trade}
                </span>
                <span className="ml-auto text-xs font-bold text-gray-700">{formatVal(lead.value)}</span>
              </div>
              <p className="text-xs font-semibold text-gray-800 line-clamp-2">{lead.title}</p>
              <p className="text-xs text-gray-400 mt-1 truncate">📍 {lead.addr}</p>
            </Link>
          ))}
        </div>
        {leads.length > 9 && (
          <Link to="/leads" className="mt-3 inline-flex items-center text-sm text-primary-600 hover:underline">
            View all {leads.length} leads →
          </Link>
        )}
      </div>
    </div>
  );
}
