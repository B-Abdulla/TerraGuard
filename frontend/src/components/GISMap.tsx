import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap, Polygon } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix typical Leaflet icon issues in React
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom Icons
export const alertIcon = new L.Icon({
    iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2VmNDQ0NCI+PHBhdGggZD0iTTEyIDBMMCAyNGgyNHoiLz48L3N2Zz4=',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
});

export const reportIcon = new L.Icon({
    iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2VhYjMwOCI+PHBhdGggZD0iTTEyIDJhMTAgMTAgMCAxIDAgMCAyMCAxMCAxMCAwIDAgMCAwLTIwek0xMSAxNmgydjJoLTJ2LTJ6bTAtMTBoMnY4aC0ydi04eiIvPjwvc3ZnPg==',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
});

export const userIcon = new L.Icon({
    iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzNiODJmNiI+PHBhdGggZD0iTTEyIDJDMiAyIDIgMTIgMiAxMmMwIDEwIDEwIDEwIDEwIDEwczEwIDAgMTAtMTAgMC0xMC0xMC0xMHptMCAxOGMtNC40MSAwLTgtMy41OS04LThzMy41OS04IDgtOCA4IDMuNTkgOCA4LTMuNTkgOC04IDh6Ii8+PHBhdGggZD0iTTEyIDZjLTIuMjEgMC00IDEuNzktNCA0czEuNzkgNCA0  NCA0LTEuNzkgNC00LTEuNzktNC00LTR6Ii8+PC9zdmc+',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
});

function MapRecenter({ center }: { center: [number, number] }) {
    const map = useMap();
    useEffect(() => {
        map.setView(center, map.getZoom());
    }, [center, map]);
    return null;
}

interface GISMapProps {
    center: [number, number];
    zoom?: number;
    zones?: any[];
    reports?: any[];
    users?: any[];
    height?: string;
}

const colorMap: Record<string, string> = {
    LOW: '#22c55e',
    MODERATE: '#eab308',
    HIGH: '#f97316',
    CRITICAL: '#ef4444'
};

export default function GISMap({ center, zoom = 11, zones = [], reports = [], users = [], height = "500px" }: GISMapProps) {
    return (
        <div style={{ height, width: '100%', borderRadius: '0.75rem', overflow: 'hidden' }} className="border border-slate-700 shadow-xl">
            <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" // Dark map tile
                />
                <MapRecenter center={center} />

                {/* Render Risk Zones */}
                {zones.map((zone) => {
                    const color = colorMap[zone.risk_level] || colorMap.MODERATE;
                    // If the backend returns standard Polygon coordinates in geojson
                    if (zone.geometry_geojson && zone.geometry_geojson.type === "Polygon") {
                        // GeoJSON is [lon, lat], Leaflet wants [lat, lon]
                        const positions = zone.geometry_geojson.coordinates[0].map((c: any) => [c[1], c[0]]);
                        return (
                            <Polygon key={zone.id} positions={positions} pathOptions={{ color, fillColor: color, fillOpacity: 0.2, weight: 2 }}>
                                <Popup>
                                    <div className="font-sans">
                                        <h3 className="font-bold text-slate-100">{zone.name}</h3>
                                        <p className="text-slate-300 text-sm mt-1">Risk Score: <span className="font-mono text-terra-400">{zone.risk_score.toFixed(2)}</span></p>
                                        <p className={`text-sm mt-1 font-bold ${zone.risk_level === 'CRITICAL' ? 'text-red-500' : 'text-orange-500'}`}>Level: {zone.risk_level}</p>
                                        <p className="text-slate-400 text-xs mt-2">Targeting: {zone.affected_users_count} users affected</p>
                                    </div>
                                </Popup>
                            </Polygon>
                        )
                    } else {
                        // Fallback to circle
                        return (
                            <Circle
                                key={zone.id}
                                center={[zone.center_lat, zone.center_lng]}
                                pathOptions={{ color: colorMap[zone.risk_level], fillColor: colorMap[zone.risk_level] }}
                                radius={zone.radius_km * 1000}
                            >
                                <Popup>
                                    <strong>{zone.name}</strong><br />Risk: {zone.risk_level} ({zone.risk_score})
                                </Popup>
                            </Circle>
                        )
                    }
                })}

                {/* Render Users */}
                {users.map(u => (
                    <Marker key={u.id} position={[u.latitude, u.longitude]} icon={userIcon}>
                        <Popup>
                            <strong>{u.full_name}</strong><br />
                            {u.phone_number}
                        </Popup>
                    </Marker>
                ))}

                {/* Render Reports */}
                {reports.map((r) => (
                    <Marker key={r.id} position={[r.latitude, r.longitude]} icon={reportIcon}>
                        <Popup>
                            <div className="font-sans">
                                <strong>{r.category.replace('_', ' ')}</strong>
                                <p className="text-xs text-slate-400 mt-1">{r.description}</p>
                                <p className="mt-2 font-bold text-xs">Status: {r.status}</p>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}
