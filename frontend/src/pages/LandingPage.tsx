import { Link } from 'react-router-dom';

export default function LandingPage() {
    return (
        <div className="w-full flex flex-col items-center justify-center pt-12 pb-24 text-center">

            <div className="max-w-4xl px-4 flex flex-col items-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-terra-400 text-sm font-mono mb-8 animate-pulse">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-terra-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-terra-500"></span>
                    </span>
                    PROTOTYPE v1.0 ONLINE
                </div>

                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white mb-6">
                    AI-Powered Landslide Risk<br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-terra-300 to-terra-500">Monitoring & Early Warning</span>
                </h1>

                <p className="text-lg md:text-xl text-slate-300 mb-10 max-w-2xl mx-auto leading-relaxed">
                    TerraGuard transforms environmental data into location-aware landslide risk estimates.
                    We identify affected users, communicate targeted warnings through SMS, and incorporate community observations for Northeast India.
                </p>

                <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
                    <Link to="/register" className="btn-primary text-lg w-full sm:w-48 text-center flex items-center justify-center gap-2">
                        Get Started
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                    </Link>
                    <Link to="/login" className="btn-secondary text-lg w-full sm:w-48 text-center">
                        Login
                    </Link>
                </div>
            </div>

            <div className="mt-24 w-full max-w-5xl mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { title: 'AI Prediction', desc: 'XGBoost engine predicting landslide risk from multi-source environmental data.' },
                    { title: 'Geospatial Targeting', desc: 'PostGIS spatial analytics identifying exactly who is inside danger zones.' },
                    { title: 'Local Early Warning', desc: 'Automated SMS alerts dispatched exclusively to affected people via Twilio.' }
                ].map((item, i) => (
                    <div key={i} className="card text-left">
                        <h3 className="text-terra-400 font-semibold text-xl mb-3">{item.title}</h3>
                        <p className="text-slate-400">{item.desc}</p>
                    </div>
                ))}
            </div>

            <div className="mt-24 w-full max-w-4xl mx-auto border-t border-slate-800 pt-16">
                <h2 className="text-2xl font-bold tracking-tight mb-8">End-to-End Decision Architecture</h2>
                <div className="flex flex-wrap items-center justify-center gap-2 text-sm font-mono text-slate-300">
                    <span className="card px-3 py-1 bg-slate-800">DATA</span> →
                    <span className="card px-3 py-1 bg-slate-800">AI RISK</span> →
                    <span className="card px-3 py-1 bg-slate-800">RISK ZONE</span> →
                    <span className="card px-3 py-1 border-terra-500/50 text-terra-300">TARGETING</span> →
                    <span className="card px-3 py-1 bg-slate-800">ALERT</span> →
                    <span className="card px-3 py-1 bg-slate-800">REPORTS</span>
                </div>
            </div>

        </div>
    );
}
