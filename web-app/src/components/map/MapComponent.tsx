'use client';

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';

interface Zone {
  type: string;
  properties: {
    GEOID: string;
    NAME: string;
    COUNTY_NAME?: string;
    score?: number;
  };
  geometry: any;
}

interface Target {
  id: string;
  lat: number;
  lng: number;
  address: string;
  score: number;
  lmi: boolean;
  kwh: number;
  owner: boolean;
  sqft: number;
  year: number;
}

interface MapComponentProps {
  zones: Zone[];
  targets: Target[];
  showLMI: boolean;
  showTargets: boolean;
  showRoute: boolean;
  onTargetClick?: (target: Target) => void;
}

export default function MapComponent({
  zones,
  targets,
  showLMI,
  showTargets,
  showRoute,
  onTargetClick
}: MapComponentProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const zoneLayerRef = useRef<L.GeoJSON | null>(null);
  const markerLayerRef = useRef<L.LayerGroup | null>(null);
  const routeLayerRef = useRef<L.Polyline | null>(null);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Virginia center
    const map = L.map(mapContainerRef.current, {
      center: [37.5, -77.5],
      zoom: 9,
      zoomControl: true,
    });

    // Base layers
    const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap'
    });

    const lightLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; CartoDB'
    });

    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri'
    });

    lightLayer.addTo(map);

    L.control.layers({
      'Light': lightLayer,
      'Street': streetLayer,
      'Satellite': satelliteLayer
    }).addTo(map);

    // GPS locate control
    const locateBtn = L.Control.extend({
      options: { position: 'topleft' },
      onAdd: function() {
        const btn = L.DomUtil.create('button', 'leaflet-bar leaflet-control');
        btn.innerHTML = '📍';
        btn.style.cssText = 'width:34px;height:34px;font-size:18px;cursor:pointer;background:white;border:none;';
        btn.title = 'Find my location';
        btn.onclick = (e) => {
          e.stopPropagation();
          navigator.geolocation.getCurrentPosition(
            (pos) => {
              const loc: [number, number] = [pos.coords.latitude, pos.coords.longitude];
              setUserLocation(loc);
              map.setView(loc, 15);
              L.marker(loc, {
                icon: L.divIcon({
                  className: 'user-marker',
                  html: '<div style="background:#4285f4;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>',
                  iconSize: [22, 22],
                  iconAnchor: [11, 11]
                })
              }).addTo(map).bindPopup('You are here');
            },
            (err) => alert('Could not get location: ' + err.message),
            { enableHighAccuracy: true }
          );
        };
        return btn;
      }
    });
    new locateBtn().addTo(map);

    mapRef.current = map;
    markerLayerRef.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update LMI zones layer
  useEffect(() => {
    if (!mapRef.current) return;

    if (zoneLayerRef.current) {
      mapRef.current.removeLayer(zoneLayerRef.current);
      zoneLayerRef.current = null;
    }

    if (showLMI && zones.length > 0) {
      const geojson = {
        type: 'FeatureCollection',
        features: zones
      };

      zoneLayerRef.current = L.geoJSON(geojson as any, {
        style: {
          fillColor: '#2563eb',
          color: '#1d4ed8',
          weight: 1.5,
          fillOpacity: 0.35
        },
        onEachFeature: (feature, layer) => {
          const props = feature.properties;
          layer.bindTooltip(
            `<strong>${props.NAME || 'Zone'}</strong><br/>
             GEOID: ${props.GEOID || 'N/A'}<br/>
             ${props.COUNTY_NAME ? 'County: ' + props.COUNTY_NAME : ''}`,
            { sticky: true }
          );
        }
      }).addTo(mapRef.current);

      // Fit to zones
      const bounds = zoneLayerRef.current.getBounds();
      if (bounds.isValid()) {
        mapRef.current.fitBounds(bounds, { padding: [20, 20] });
      }
    }
  }, [zones, showLMI]);

  // Update target markers
  useEffect(() => {
    if (!mapRef.current || !markerLayerRef.current) return;

    markerLayerRef.current.clearLayers();

    if (showTargets && targets.length > 0) {
      targets.forEach((target, idx) => {
        const color = target.score >= 80 ? '#22c55e' : target.score >= 60 ? '#eab308' : '#6b7280';

        const marker = L.marker([target.lat, target.lng], {
          icon: L.divIcon({
            className: 'target-marker',
            html: `<div style="
              background:${color};
              color:white;
              width:28px;
              height:28px;
              border-radius:50%;
              display:flex;
              align-items:center;
              justify-content:center;
              font-weight:bold;
              font-size:11px;
              border:2px solid white;
              box-shadow:0 2px 4px rgba(0,0,0,0.3);
            ">${target.score}</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
          })
        });

        marker.bindPopup(`
          <div style="min-width:200px;">
            <strong style="font-size:14px;">${target.address}</strong><br/>
            <hr style="margin:8px 0;"/>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:12px;">
              <span>Score:</span><strong style="color:${color}">${target.score}</strong>
              <span>LMI Zone:</span><strong>${target.lmi ? '✅ Yes' : '❌ No'}</strong>
              <span>kWh/mo:</span><strong>${target.kwh}</strong>
              <span>Owner:</span><strong>${target.owner ? '✅' : '🏠 Rent'}</strong>
              <span>Sq Ft:</span><strong>${target.sqft.toLocaleString()}</strong>
              <span>Year Built:</span><strong>${target.year}</strong>
            </div>
            <button onclick="window.selectTarget && window.selectTarget('${target.id}')"
              style="width:100%;margin-top:10px;padding:8px;background:#2563eb;color:white;border:none;border-radius:4px;cursor:pointer;">
              Add to Route
            </button>
          </div>
        `);

        marker.on('click', () => onTargetClick?.(target));
        marker.addTo(markerLayerRef.current!);
      });
    }
  }, [targets, showTargets, onTargetClick]);

  // Update route line
  useEffect(() => {
    if (!mapRef.current) return;

    if (routeLayerRef.current) {
      mapRef.current.removeLayer(routeLayerRef.current);
      routeLayerRef.current = null;
    }

    if (showRoute && targets.length > 1) {
      // Sort targets by score for optimal route
      const sorted = [...targets].sort((a, b) => b.score - a.score);
      const coords: [number, number][] = sorted.map(t => [t.lat, t.lng]);

      // Draw route line
      routeLayerRef.current = L.polyline(coords, {
        color: '#ef4444',
        weight: 3,
        opacity: 0.8,
        dashArray: '10, 10'
      }).addTo(mapRef.current);

      // Add numbered markers for route order
      sorted.forEach((target, idx) => {
        L.marker([target.lat, target.lng], {
          icon: L.divIcon({
            className: 'route-number',
            html: `<div style="
              background:#ef4444;
              color:white;
              width:20px;
              height:20px;
              border-radius:50%;
              display:flex;
              align-items:center;
              justify-content:center;
              font-weight:bold;
              font-size:11px;
              border:2px solid white;
              position:relative;
              top:-30px;
              left:10px;
            ">${idx + 1}</div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
          }),
          interactive: false
        }).addTo(mapRef.current!);
      });
    }
  }, [targets, showRoute]);

  return (
    <div
      ref={mapContainerRef}
      style={{ width: '100%', height: '100%', minHeight: '500px' }}
    />
  );
}
