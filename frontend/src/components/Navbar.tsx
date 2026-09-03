import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Navbar() {
    const { user, isAuth, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    return (
        <nav className="w-full bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex justify-between items-center flex-wrap gap-4">

                    <Link to="/" className="flex items-center gap-2 group">
                        <div className="w-8 h-8 rounded-lg bg-terra-500 flex items-center justify-center text-slate-950 font-bold text-xl group-hover:bg-terra-400 transition-colors shadow-lg shadow-terra-500/20">
                            T
                        </div>
                        <span className="text-xl font-bold tracking-tight text-white group-hover:text-terra-400 transition-colors">
                            TERRAGUARD
                        </span>
                    </Link>

                    <div className="flex items-center gap-4 text-sm font-medium">
                        {isAuth ? (
                            <>
                                <span className="hidden md:inline-block px-3 py-1 rounded bg-slate-800 border border-slate-700 text-slate-300">
                                    {user?.full_name} <span className="opacity-50 ml-2 text-xs font-mono">{user?.role}</span>
                                </span>

                                {user?.role === 'RESIDENT' && (
                                    <Link to="/dashboard" className="text-slate-300 hover:text-white transition-colors">Dashboard</Link>
                                )}

                                {['AUTHORITY', 'ADMIN', 'RESPONSE_TEAM'].includes(user?.role || '') && (
                                    <>
                                        <Link to="/command-center" className="text-slate-300 hover:text-white transition-colors">Command Center</Link>
                                        <Link to="/system-health" className="text-slate-300 hover:text-white transition-colors">Health</Link>
                                    </>
                                )}

                                <button onClick={handleLogout} className="text-red-400 hover:text-red-300 transition-colors">
                                    Logout
                                </button>
                            </>
                        ) : (
                            <>
                                <Link to="/login" className="text-slate-300 hover:text-white transition-colors">Login</Link>
                                <Link to="/register" className="btn-primary py-1.5 px-4 text-sm">Register</Link>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
}
