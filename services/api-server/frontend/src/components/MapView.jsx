import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';

// Fix default marker icon issue with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom colored marker icon
function createColoredIcon(color = '#4f46e5') {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <svg width="28" height="40" viewBox="0 0 28 40" xmlns="http://www.w3.org/2000/svg">
        <path d="M14 0C6.268 0 0 6.268 0 14c0 10.5 14 26 14 26s14-15.5 14-26C28 6.268 21.732 0 14 0z" fill="${color}" stroke="white" stroke-width="2"/>
        <circle cx="14" cy="14" r="6" fill="white" opacity="0.9"/>
      </svg>
    `,
    iconSize: [28, 40],
    iconAnchor: [14, 40],
    popupAnchor: [0, -40],
  });
}

// Component that adjusts map bounds to fit all markers
function FitBounds({ markers }) {
  const map = useMap();

  useEffect(() => {
    if (markers && markers.length > 0) {
      const validMarkers = markers.filter(
        (m) => m.lat && m.lng && !isNaN(m.lat) && !isNaN(m.lng)
      );
      if (validMarkers.length > 0) {
        const bounds = L.latLngBounds(
          validMarkers.map((m) => [m.lat, m.lng])
        );
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
      }
    }
  }, [markers, map]);

  return null;
}

export default function MapView({
  markers = [],
  center = [39.8283, -98.5795],
  zoom = 4,
  height = '400px',
  className = '',
  markerColor = '#4f46e5',
}) {
  const customIcon = createColoredIcon(markerColor);

  const validMarkers = markers.filter(
    (m) => m.lat && m.lng && !isNaN(Number(m.lat)) && !isNaN(Number(m.lng))
  );

  return (
    <div className={`rounded-xl overflow-hidden ring-1 ring-gray-200 ${className}`} style={{ height }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {validMarkers.length > 0 && <FitBounds markers={validMarkers} />}
        {validMarkers.map((marker, index) => (
          <Marker
            key={marker.id || index}
            position={[Number(marker.lat), Number(marker.lng)]}
            icon={customIcon}
          >
            {marker.label && (
              <Popup>
                <div className="text-sm">
                  <p className="font-semibold text-gray-900">{marker.label}</p>
                  {marker.sublabel && (
                    <p className="text-gray-500 mt-1">{marker.sublabel}</p>
                  )}
                  {marker.value && (
                    <p className="text-primary-600 font-medium mt-1">{marker.value}</p>
                  )}
                </div>
              </Popup>
            )}
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
