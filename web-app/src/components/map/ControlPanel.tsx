'use client';

import { useState } from 'react';

interface Target {
  id: string;
  address: string;
  score: number;
  lmi: boolean;
  kwh: number;
  owner: boolean;
}

interface ControlPanelProps {
  showLMI: boolean;
  setShowLMI: (v: boolean) => void;
  showTargets: boolean;
  setShowTargets: (v: boolean) => void;
  showRoute: boolean;
  setShowRoute: (v: boolean) => void;
  routeTargets: Target[];
  onPrintStreetSheet: () => void;
  onClearRoute: () => void;
}

// Common rebuttals and scripts
const SCRIPTS = {
  intro: `Hi! I'm [NAME] with EMG Solar. We're helping homeowners in this neighborhood save money on electricity through the state's solar program. Are you the homeowner?`,

  lmi_benefit: `Great news - your address is in an LMI qualifying zone, which means you automatically qualify for additional state incentives worth up to $6,000!`,

  objections: {
    'not interested': `I totally understand. Just to clarify - this isn't a sales pitch today. We're just confirming which homes in this LMI zone qualify for the state benefit before the deadline. Can I leave you this info?`,

    'renting': `No problem! Do you happen to know if your landlord would be interested? We can leave information for them.`,

    'already have solar': `That's great you went solar! Are you getting the full LMI benefit? Many homeowners aren't aware they qualify for additional credits.`,

    'too expensive': `Actually, with the LMI zone benefit plus federal credits, most homeowners see zero out of pocket cost. The state program covers installation.`,

    'need to think': `Of course! Here's my card. The state benefit does have a deadline though - would tomorrow or the next day work better for a quick 10-minute review?`,

    'bad credit': `That's actually not a problem for this program. The state benefit is based on your location, not credit score. Let me show you how it works.`
  }
};

export default function ControlPanel({
  showLMI,
  setShowLMI,
  showTargets,
  setShowTargets,
  showRoute,
  setShowRoute,
  routeTargets,
  onPrintStreetSheet,
  onClearRoute
}: ControlPanelProps) {
  const [activeTab, setActiveTab] = useState<'layers' | 'route' | 'scripts'>('layers');
  const [expandedScript, setExpandedScript] = useState<string | null>(null);

  return (
    <div style={{
      position: 'absolute',
      top: '10px',
      right: '10px',
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.15)',
      width: '320px',
      maxHeight: 'calc(100vh - 100px)',
      overflow: 'hidden',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #e5e7eb' }}>
        {(['layers', 'route', 'scripts'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              flex: 1,
              padding: '12px 8px',
              border: 'none',
              background: activeTab === tab ? '#2563eb' : 'white',
              color: activeTab === tab ? 'white' : '#374151',
              cursor: 'pointer',
              fontWeight: activeTab === tab ? 'bold' : 'normal',
              fontSize: '13px',
              textTransform: 'capitalize'
            }}
          >
            {tab === 'layers' ? '🗺️ Layers' : tab === 'route' ? '🚶 Route' : '📝 Scripts'}
          </button>
        ))}
      </div>

      <div style={{ padding: '12px', overflow: 'auto', flex: 1 }}>
        {/* Layers Tab */}
        {activeTab === 'layers' && (
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showLMI}
                onChange={(e) => setShowLMI(e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
              <span>
                <strong style={{ color: '#2563eb' }}>■</strong> LMI Auto-Qualify Zones
              </span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showTargets}
                onChange={(e) => setShowTargets(e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
              <span>
                <strong style={{ color: '#22c55e' }}>●</strong> Target Addresses
              </span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={showRoute}
                onChange={(e) => setShowRoute(e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
              <span>
                <strong style={{ color: '#ef4444' }}>⋯</strong> Walking Route
              </span>
            </label>

            <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid #e5e7eb' }} />

            <div style={{ fontSize: '12px', color: '#6b7280' }}>
              <strong>Score Legend:</strong>
              <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
                <span><span style={{ color: '#22c55e' }}>●</span> 80+ Hot</span>
                <span><span style={{ color: '#eab308' }}>●</span> 60-79 Warm</span>
                <span><span style={{ color: '#6b7280' }}>●</span> &lt;60 Cold</span>
              </div>
            </div>
          </div>
        )}

        {/* Route Tab */}
        {activeTab === 'route' && (
          <div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <button
                onClick={onPrintStreetSheet}
                disabled={routeTargets.length === 0}
                style={{
                  flex: 1,
                  padding: '10px',
                  background: routeTargets.length > 0 ? '#2563eb' : '#d1d5db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: routeTargets.length > 0 ? 'pointer' : 'not-allowed',
                  fontWeight: 'bold'
                }}
              >
                🖨️ Print Street Sheet
              </button>
              <button
                onClick={onClearRoute}
                disabled={routeTargets.length === 0}
                style={{
                  padding: '10px 16px',
                  background: '#fee2e2',
                  color: '#dc2626',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: routeTargets.length > 0 ? 'pointer' : 'not-allowed'
                }}
              >
                Clear
              </button>
            </div>

            {routeTargets.length === 0 ? (
              <p style={{ color: '#6b7280', fontSize: '13px', textAlign: 'center', padding: '20px' }}>
                Click targets on map to add to route
              </p>
            ) : (
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
                  Walking Route ({routeTargets.length} stops)
                </div>
                {routeTargets.map((t, idx) => (
                  <div
                    key={t.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px',
                      background: idx % 2 === 0 ? '#f9fafb' : 'white',
                      borderRadius: '4px',
                      marginBottom: '4px'
                    }}
                  >
                    <span style={{
                      background: '#ef4444',
                      color: 'white',
                      width: '22px',
                      height: '22px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '11px',
                      fontWeight: 'bold'
                    }}>
                      {idx + 1}
                    </span>
                    <div style={{ flex: 1, fontSize: '12px' }}>
                      <div style={{ fontWeight: '500' }}>{t.address}</div>
                      <div style={{ color: '#6b7280' }}>
                        Score: {t.score} | {t.lmi ? 'LMI ✓' : ''} {t.owner ? 'Owner ✓' : 'Renter'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Scripts Tab */}
        {activeTab === 'scripts' && (
          <div style={{ fontSize: '13px' }}>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '6px', color: '#2563eb' }}>
                🎯 Opening Script
              </div>
              <div style={{
                background: '#eff6ff',
                padding: '10px',
                borderRadius: '6px',
                lineHeight: '1.5'
              }}>
                {SCRIPTS.intro}
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '6px', color: '#22c55e' }}>
                ✅ LMI Zone Benefit
              </div>
              <div style={{
                background: '#f0fdf4',
                padding: '10px',
                borderRadius: '6px',
                lineHeight: '1.5'
              }}>
                {SCRIPTS.lmi_benefit}
              </div>
            </div>

            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
              💬 Common Objections
            </div>
            {Object.entries(SCRIPTS.objections).map(([objection, response]) => (
              <div key={objection} style={{ marginBottom: '6px' }}>
                <button
                  onClick={() => setExpandedScript(expandedScript === objection ? null : objection)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '8px 10px',
                    background: '#f3f4f6',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <span style={{ textTransform: 'capitalize' }}>"{objection}"</span>
                  <span>{expandedScript === objection ? '▼' : '▶'}</span>
                </button>
                {expandedScript === objection && (
                  <div style={{
                    padding: '10px',
                    background: '#fef3c7',
                    borderRadius: '0 0 4px 4px',
                    lineHeight: '1.5',
                    marginTop: '-2px'
                  }}>
                    {response}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
