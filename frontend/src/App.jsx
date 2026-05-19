import React from 'react';
import SmartCityDashboard from '../../SmartCityDashboard';

function App() {
  return (
    <div className="w-full min-h-screen bg-slate-950 text-slate-100 selection:bg-blue-500/30">
      {/* Renders the complete Smart City Distributed Systems dashboard layout */}
      <SmartCityDashboard />
    </div>
  );
}

export default App;