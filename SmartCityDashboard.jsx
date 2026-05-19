import React, { useState, useEffect } from 'react';

// --- Custom UI Components to replace external libraries ---
const Card = ({ children, className = '' }) => (
  <div className={`bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl ${className}`}>
    {children}
  </div>
);

const Badge = ({ children, variant = 'info' }) => {
  const styles = {
    info: 'bg-blue-900/40 text-blue-400 border-blue-800',
    success: 'bg-emerald-950 text-emerald-400 border-emerald-800',
    warning: 'bg-amber-950 text-amber-400 border-amber-800',
    danger: 'bg-rose-950 text-rose-400 border-rose-800',
  };
  return (
    <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${styles[variant]}`}>
      {children}
    </span>
  );
};

export default function SmartCityDashboard() {
  // Connection and system status state
  const [isConnected, setIsConnected] = useState(true);
  const [useMockData, setUseMockData] = useState(true);
  const [systemState, setSystemState] = useState({
    lamport: 42,
    events: [
      { id: 1, time: '10:41:02', text: '[SENSOR] Traffic data published from Node-A' },
      { id: 2, time: '10:41:05', text: '[BROKER] Routed traffic data to traffic_police' },
      { id: 3, time: '10:41:12', text: '[SENSOR] Water level spike detected in Zone-4' },
    ],
    subscribers: {
      'traffic': ['traffic_police', 'transit_control'],
      'weather': ['disaster_mgmt'],
      'grid': ['power_utility'],
    },
    transactions: [
      { tx_id: 'TX-888', status: 'COMMITTED', type: '2PC-Lite', participants: ['traffic_police'] },
      { tx_id: 'TX-889', status: 'PREPARED', type: '2PC-Lite', participants: ['disaster_mgmt', 'traffic_police'] }
    ]
  });

  // Simulation loop for mock data to show it dynamically working
  useEffect(() => {
    if (!useMockData) return;

    const interval = setInterval(() => {
      setSystemState(prev => {
        // Step clock forward
        const nextClock = prev.lamport + Math.floor(Math.random() * 3) + 1;
        
        // Generate a new random smart city event
        const mockEventsList = [
          '[SENSOR] Air quality index updated for Downtown',
          '[MUTEX] Lock released on topic: grid',
          '[BROKER] Dynamic routing tables synchronized',
          '[2PC] Coordinator initiating vote for TX-890',
          '[SENSOR] Emergency vehicle bypass requested on Route 9'
        ];
        const randomEventText = mockEventsList[Math.floor(Math.random() * mockEventsList.length)];
        const timestamp = new Date().toLocaleTimeString();
        
        const newEvent = {
          id: Date.now(),
          time: timestamp,
          text: randomEventText
        };

        // Randomly update transactions status
        const updatedTx = prev.transactions.map(tx => {
          if (tx.status === 'PREPARED' && Math.random() > 0.5) {
            return { ...tx, status: 'COMMITTED' };
          }
          return tx;
        });

        // Add a new transaction occasionally
        if (Math.random() > 0.7) {
          const idNum = Math.floor(Math.random() * 900) + 100;
          updatedTx.unshift({
            tx_id: `TX-${idNum}`,
            status: 'PREPARED',
            type: '2PC-Lite',
            participants: ['disaster_mgmt']
          });
        }

        return {
          lamport: nextClock,
          events: [newEvent, ...prev.events.slice(0, 4)],
          subscribers: prev.subscribers,
          transactions: updatedTx.slice(0, 4)
        };
      });
    }, 2500);

    return () => clearInterval(interval);
  }, [useMockData]);

  // Real production polling engine toggle (for connecting to your Python bridge)
  useEffect(() => {
    if (useMockData) return;

    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/status');
        const data = await response.json();
        setSystemState(data);
        setIsConnected(true);
      } catch (err) {
        setIsConnected(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [useMockData]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-6">
      
      {/* Header Bar */}
      <header className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-5 mb-8 gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            SMART CITY LIVE DS OPERATIONS DASHBOARD
          </h1>
          <p className="text-xs text-slate-400 mt-1">Distributed Pub-Sub Architecture Tracking System</p>
        </div>
        
        {/* Environment Control Node */}
        <div className="flex items-center gap-4 bg-slate-900 border border-slate-800 rounded-lg p-2.5 self-start">
          <div className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
            <span className="text-xs font-mono font-medium text-slate-300">
              {isConnected ? 'NODE_CONNECTED' : 'NODE_DISCONNECTED'}
            </span>
          </div>
          <div className="h-4 w-px bg-slate-800" />
          <button 
            onClick={() => setUseMockData(!useMockData)}
            className={`text-xs font-semibold px-3 py-1 rounded transition-all ${
              useMockData 
                ? 'bg-amber-950/50 text-amber-400 border border-amber-800' 
                : 'bg-blue-950 text-blue-400 border border-blue-800'
            }`}
          >
            {useMockData ? '🔴 Running Mock Stream' : '🔗 Polling localhost:5000'}
          </button>
        </div>
      </header>

      {/* Primary 4-Panel Grid layout */}
      <main className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* PANEL 1: RPC Model Data Logs */}
        <Card>
          <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-2">
            <h2 className="text-sm font-bold tracking-wider text-slate-400 uppercase font-mono">
              [PANEL 1: RPC MODEL DATA LOGS]
            </h2>
            <Badge variant="info">Pub-Sub Pipe</Badge>
          </div>
          <div className="space-y-2.5 max-h-[220px] overflow-y-auto font-mono text-sm">
            {systemState.events.map((event) => (
              <div key={event.id} className="flex gap-3 bg-slate-950/50 p-2.5 rounded border border-slate-900">
                <span className="text-blue-500 text-xs shrink-0 select-none">[{event.time}]</span>
                <span className="text-slate-300 break-all">{event.text}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* PANEL 2: Logical System Clocks */}
        <Card className="flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-2">
              <h2 className="text-sm font-bold tracking-wider text-slate-400 uppercase font-mono">
                [PANEL 2: LOGICAL SYSTEM CLOCKS]
              </h2>
              <Badge variant="warning">Lamport Sequence</Badge>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              Causality tracking across decoupled distributed city nodes without hardware NTP time sync dependency.
            </p>
          </div>
          <div className="bg-slate-950 rounded-xl border border-slate-800 p-6 flex flex-col items-center justify-center text-center my-auto">
            <span className="text-xs font-mono tracking-widest text-slate-500 uppercase font-bold">
              Current Broker Logical Clock
            </span>
            <span className="text-5xl font-mono font-black text-amber-400 tracking-tight my-2 drop-shadow-[0_0_12px_rgba(251,191,36,0.15)]">
              {systemState.lamport}
            </span>
            <span className="text-[10px] font-mono text-emerald-500 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/60">
              CLOCK_TICK_LATEST = L + 1
            </span>
          </div>
        </Card>

        {/* PANEL 3: Mutex Operations Registry */}
        <Card>
          <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-2">
            <h2 className="text-sm font-bold tracking-wider text-slate-400 uppercase font-mono">
              [PANEL 3: MUTEX OPERATIONS REGISTRY]
            </h2>
            <Badge variant="success">Active Leases</Badge>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Monitoring topic locking mechanisms and consumer groups registered under distributed exclusions.
          </p>
          <div className="space-y-3 font-mono text-sm">
            {Object.entries(systemState.subscribers).map(([topic, consumers]) => (
              <div key={topic} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-slate-950/60 rounded border border-slate-850 gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">TOPIC:</span>
                  <span className="text-emerald-400 font-bold font-mono">'{topic}'</span>
                </div>
                <div className="flex flex-wrap gap-1.5 items-center">
                  <span className="text-[11px] text-slate-500 mr-1">ACTIVE_LOCKS:</span>
                  {consumers.map((sub, i) => (
                    <span key={i} className="text-xs bg-slate-900 border border-slate-700 text-slate-200 px-2 py-0.5 rounded">
                      {sub}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* PANEL 4: Distributed Transactions Log */}
        <Card>
          <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-2">
            <h2 className="text-sm font-bold tracking-wider text-slate-400 uppercase font-mono">
              [PANEL 4: DISTRIBUTED TRANSACTIONS LOG (2PC-lite)]
            </h2>
            <Badge variant={systemState.transactions.some(t => t.status === 'PREPARED') ? 'warning' : 'success'}>
              Atomic Consensus
            </Badge>
          </div>
          <div className="space-y-2.5 font-mono text-sm">
            {systemState.transactions.length > 0 ? (
              systemState.transactions.map((tx) => (
                <div key={tx.tx_id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 bg-slate-950/40 rounded border border-slate-900 gap-2">
                  <div className="flex flex-col">
                    <span className="text-xs font-bold text-slate-300">{tx.tx_id} <span className="text-[10px] font-normal text-slate-500">({tx.type})</span></span>
                    <span className="text-[11px] text-slate-500 mt-0.5">Participants: {tx.participants.join(', ')}</span>
                  </div>
                  <div className="sm:self-center">
                    <Badge variant={tx.status === 'COMMITTED' ? 'success' : 'warning'}>
                      {tx.status === 'COMMITTED' ? '✅ COMMITTED' : '⏳ PREPARED'}
                    </Badge>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center p-6 text-slate-500 text-xs italic">
                No active atomic operations found.
              </div>
            )}
          </div>
        </Card>

      </main>

      {/* Decorative Console Footer Wrapper */}
      <footer className="mt-8 text-center text-[11px] font-mono text-slate-600 border-t border-slate-900 pt-4">
        SYSTEM ENGINE CONTRACT LAYER v1.0.4 • SECURE DISTRIBUTED SYSTEM BUFFER
      </footer>
    </div>
  );
}