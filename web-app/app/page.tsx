'use client';

import { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import ControlPanel from '@/components/map/ControlPanel';

// Dynamic import for Leaflet (no SSR)
const MapComponent = dynamic(() => import('@/components/map/MapComponent'), {
  ssr: false,
  loading: () => (
    <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f3f4f6' }}>
      <div>Loading map...</div>
    </div>
  )
});

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

export default function Home() {
  const [zones, setZones] = useState<any[]>([]);
  const [targets, setTargets] = useState<Target[]>([]);
  const [loading, setLoading] = useState(true);
  const [showLMI, setShowLMI] = useState(true);
  const [showTargets, setShowTargets] = useState(true);
  const [showRoute, setShowRoute] = useState(false);
  const [routeTargets, setRouteTargets] = useState<Target[]>([]);
  const [currentView, setCurrentView] = useState<'map' | 'sheet'>('map');
  const [stats, setStats] = useState({ doors: 0, deals: 0, callbacks: 0 });

  // Load zones and targets on mount
  useEffect(() => {
    Promise.all([
      fetch('/data/blue_zones.geojson').then(r => r.json()).catch(() => ({ features: [] })),
      fetch('/data/ranked_targets.json').then(r => r.json()).catch(() => [])
    ]).then(([zoneData, targetData]) => {
      if (zoneData.features) {
        setZones(zoneData.features);
      }
      if (targetData.length > 0) {
        setTargets(targetData);
      }
      setLoading(false);
    });
  }, []);

  // Handle target click - add to route
  const handleTargetClick = (target: Target) => {
    if (routeTargets.find(t => t.id === target.id)) {
      // Remove from route
      setRouteTargets(routeTargets.filter(t => t.id !== target.id));
    } else {
      // Add to route
      setRouteTargets([...routeTargets, target]);
    }
  };

  // Print street sheet
  const handlePrintStreetSheet = () => {
    window.print();
  };

  // Clear route
  const handleClearRoute = () => {
    setRouteTargets([]);
    setShowRoute(false);
  };

  // Log door knock result
  const logResult = (targetId: string, result: 'deal' | 'callback' | 'ni' | 'nh') => {
    setStats(prev => ({
      doors: prev.doors + 1,
      deals: result === 'deal' ? prev.deals + 1 : prev.deals,
      callbacks: result === 'callback' ? prev.callbacks + 1 : prev.callbacks
    }));
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header className="no-print" style={{
        background: 'linear-gradient(135deg, #1e40af, #2563eb)',
        color: 'white',
        padding: '12px 16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0 }}>EMG Field Ops</h1>
          <div style={{ fontSize: '12px', opacity: 0.9 }}>Dominion Energy Virginia</div>
        </div>
        <div style={{ display: 'flex', gap: '16px', fontSize: '13px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{stats.doors}</div>
            <div style={{ opacity: 0.8 }}>Doors</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#4ade80' }}>{stats.deals}</div>
            <div style={{ opacity: 0.8 }}>Deals</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#fbbf24' }}>{stats.callbacks}</div>
            <div style={{ opacity: 0.8 }}>Callbacks</div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main style={{ flex: 1, position: 'relative' }} className="no-print">
        <MapComponent
          zones={zones}
          targets={targets}
          showLMI={showLMI}
          showTargets={showTargets}
          showRoute={showRoute}
          onTargetClick={handleTargetClick}
        />
        <ControlPanel
          showLMI={showLMI}
          setShowLMI={setShowLMI}
          showTargets={showTargets}
          setShowTargets={setShowTargets}
          showRoute={showRoute}
          setShowRoute={setShowRoute}
          routeTargets={routeTargets}
          onPrintStreetSheet={handlePrintStreetSheet}
          onClearRoute={handleClearRoute}
        />

        {/* Quick actions floating button */}
        {routeTargets.length > 0 && (
          <button
            onClick={() => setShowRoute(true)}
            style={{
              position: 'absolute',
              bottom: '20px',
              left: '50%',
              transform: 'translateX(-50%)',
              padding: '12px 24px',
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '30px',
              fontWeight: 'bold',
              fontSize: '14px',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(239,68,68,0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            🚶 Start Route ({routeTargets.length} stops)
          </button>
        )}
      </main>

      {/* Printable Street Sheet */}
      <div className="street-sheet">
        <div className="header">
          <h2>EMG Solar - Street Sheet</h2>
          <p>Date: {new Date().toLocaleDateString()} | Rep: ________________</p>
          <p>Territory: Dominion Energy Virginia - LMI Zones</p>
        </div>

        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Address</th>
              <th>Score</th>
              <th>LMI</th>
              <th>Owner</th>
              <th>kWh</th>
              <th>Result</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {(routeTargets.length > 0 ? routeTargets : targets).map((target, idx) => (
              <tr key={target.id}>
                <td>{idx + 1}</td>
                <td>{target.address}</td>
                <td style={{ fontWeight: 'bold' }}>{target.score}</td>
                <td>{target.lmi ? '✓' : ''}</td>
                <td>{target.owner ? '✓' : 'R'}</td>
                <td>{target.kwh}</td>
                <td><div className="result-box"></div></td>
                <td style={{ width: '150px' }}></td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={{ marginTop: '20px', fontSize: '11px' }}>
          <strong>Result Codes:</strong> D = Deal | CB = Callback | NI = Not Interested | NH = Not Home | R = Renter
        </div>

        <div style={{ marginTop: '15px', fontSize: '11px', borderTop: '1px solid #ccc', paddingTop: '10px' }}>
          <strong>LMI Quick Pitch:</strong> "Your address qualifies for an additional $6,000 state solar benefit because you're in an LMI zone. This covers installation costs."
        </div>
      </div>
    </div>
  );
}
