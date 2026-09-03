import { useState, useEffect } from 'react';
import api from '../api';

export default function SystemHealth() {
    const [health, setHealth] = useState<any>(null);
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [scenarioRes, setScenarioRes] = useState<any>(null);
    const [sLoading, setSLoading] = useState(false);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const [h, s] = await Promise.all([
                    api.get('/system/health'),
                    api.get('/system/stats')
                ]);
                setHealth(h.data);
                setStats(s.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchHealth();
        const int = setInterval(fetchHealth, 10000);
        return () => clearInterval(int);
    }, []);

    const runScenario = async (scenario: string) => {
        setSLoading(true);
        setScenarioRes(null);
        try {
            const res = await api.post('/system/demo-scenario', { scenario });
            setScenarioRes(res.data);
        } catch (err: any) {
            alert('Scenario failed: ' + (err.response?.data?.detail || err.message));
        } finally {
            setSLoading(false);
        }
    };

    if (loading) return <div className="text-center font-mono mt-10">LOADING_SYSTEM_TELEMETRY...</div>;

    const getStatusColor = (status: string) => {
        if (status === 'AVAILABLE') return 'text-green-400 bg-green-500/10 border-green-500/20';
        if (status === 'DEMO') return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
        if (status === 'DEGRADED') return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
        return 'text-red-400 bg-red-500/10 border-red-500/20';
    };

    return (
        <div className="w-full flex flex-col gap-6">
            <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <h1 className="text-2xl font-bold tracking-tight">System Telemetry & Health</h1>
                {health?.demo_mode && (
                    <span className="px-3 py-1 bg-yellow-500/10 border border-yellow-500/30 text-yellow-400 font-mono text-sm shadow-[0_0_15px_rgba(234,179,8,0.2)]">
                        TWILIO: DEMO MODE ACTIVE
                    </span>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Core Subsystems */}
                <div className="card">
                    <h2 className="text-lg font-bold mb-4">Core Subsystems</h2>
                    <div className="space-y-2 font-mono text-sm">
                        {Object.entries(health || {}).filter(([k]) => k !== 'demo_mode').map(([key, value]: any) => (
                            <div key={key} className="flex justify-between items-center p-2 rounded-lg bg-slate-800/50">
                                <span className="uppercase text-slate-400">{key.replace('_', ' ')}</span>
                                <span className={`px-2 py-0.5 rounded border ${getStatusColor(value)}`}>{value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Global Stats */}
                <div className="card">
                    <h2 className="text-lg font-bold mb-4">Global Statistics</h2>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 bg-slate-800/50 rounded-lg text-center">
                            <div className="text-2xl font-bold text-white">{stats?.total_users}</div>
                            <div className="text-xs text-slate-400 uppercase tracking-tighter mt-1">Users</div>
                        </div>
                        <div className="p-3 bg-slate-800/50 rounded-lg text-center">
                            <div className="text-2xl font-bold text-terra-400">{stats?.active_risk_zones}</div>
                            <div className="text-xs text-slate-400 uppercase tracking-tighter mt-1">Active Zones</div>
                        </div>
                        <div className="p-3 bg-slate-800/50 rounded-lg text-center">
                            <div className="text-2xl font-bold text-red-500">{stats?.total_alerts}</div>
                            <div className="text-xs text-slate-400 uppercase tracking-tighter mt-1">Total Alerts</div>
                        </div>
                        <div className="p-3 bg-slate-800/50 rounded-lg text-center">
                            <div className="text-2xl font-bold text-orange-400">{stats?.total_reports}</div>
                            <div className="text-xs text-slate-400 uppercase tracking-tighter mt-1">Reports</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Demo Orchestrator */}
            <div className="card border-terra-900 shadow-[0_0_30px_rgba(34,197,94,0.05)]">
                <h2 className="text-lg font-bold text-terra-400 mb-2">Simulated Demo Orchestrator</h2>
                <p className="text-sm text-slate-400 mb-6">Trigger end-to-end event chains. These will generate predictions, create risk polygons, isolate affected PostGIS users, and send Twilio DEMO_MODE alerts.</p>

                <div className="flex flex-wrap gap-3 mb-6">
                    <button onClick={() => runScenario('NORMAL')} disabled={sLoading} className="btn-secondary text-sm">NORMAL</button>
                    <button onClick={() => runScenario('MODERATE_RAINFALL')} disabled={sLoading} className="btn-secondary text-sm">MODERATE</button>
                    <button onClick={() => runScenario('HIGH_RISK')} disabled={sLoading} className="bg-orange-600 hover:bg-orange-500 text-white font-bold py-2 px-4 rounded-lg">HIGH RISK</button>
                    <button onClick={() => runScenario('CRITICAL_RISK')} disabled={sLoading} className="bg-red-600 hover:bg-red-500 text-white font-bold py-2 px-4 rounded-lg shadow-[0_0_15px_rgba(239,68,68,0.5)]">CRITICAL RISK</button>
                    <button onClick={() => runScenario('AI_FAILURE')} disabled={sLoading} className="btn-secondary text-sm ml-auto border-dashed">Simulate AI Failure</button>
                </div>

                {scenarioRes && (
                    <div className="mt-4 p-4 rounded-lg bg-slate-900 border border-slate-700 font-mono text-sm relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-1 h-full bg-terra-500"></div>
                        <h3 className="font-bold text-white mb-2">{scenarioRes.message}</h3>
                        {scenarioRes.prediction && (
                            <div className="grid grid-cols-2 gap-4 mt-4 text-slate-300">
                                <div>
                                    <p className="text-terra-400 mb-1">AI Output</p>
                                    <ul className="space-y-1">
                                        <li>Score: {scenarioRes.prediction.risk_score.toFixed(3)}</li>
                                        <li>Level: {scenarioRes.prediction.risk_level}</li>
                                        <li>Version: {scenarioRes.prediction.model_version}</li>
                                    </ul>
                                </div>
                                <div>
                                    <p className="text-terra-400 mb-1">Targeting & Comm</p>
                                    <ul className="space-y-1">
                                        <li>Zone: {scenarioRes.risk_zone?.id}</li>
                                        <li>Affected Users Found: {scenarioRes.affected_users}</li>
                                        <li>Twilio Alerts Sent: {scenarioRes.alerts_created}</li>
                                    </ul>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
