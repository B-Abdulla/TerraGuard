import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import Navbar from './components/Navbar';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import ResidentDashboard from './pages/ResidentDashboard';
import AuthorityCommandCenter from './pages/AuthorityCommandCenter';
import SystemHealth from './pages/SystemHealth';

function PrivateRoute({ children, allowedRoles }: { children: JSX.Element, allowedRoles?: string[] }) {
    const { isAuth, loading, user } = useAuth();

    if (loading) return <div className="p-10 text-center text-terra-400 font-mono">INITIALIZING_SECURE_CONNECTION...</div>;
    if (!isAuth) return <Navigate to="/login" />;

    if (allowedRoles && user && !allowedRoles.includes(user.role)) {
        return <Navigate to="/" />; // Fallback to landing if unauthorized for specific route
    }

    return children;
}

export default function App() {
    return (
        <div className="min-h-screen flex flex-col bg-slate-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950">
            <Navbar />
            <main className="flex-1 w-full max-w-7xl mx-auto p-4 md:p-6 lg:p-8 flex flex-col items-center">
                <div className="w-full">
                    <Routes>
                        <Route path="/" element={<LandingPage />} />
                        <Route path="/login" element={<Login />} />
                        <Route path="/register" element={<Register />} />

                        <Route path="/dashboard" element={
                            <PrivateRoute allowedRoles={['RESIDENT']}>
                                <ResidentDashboard />
                            </PrivateRoute>
                        } />

                        <Route path="/command-center" element={
                            <PrivateRoute allowedRoles={['AUTHORITY', 'RESPONSE_TEAM', 'ADMIN']}>
                                <AuthorityCommandCenter />
                            </PrivateRoute>
                        } />

                        <Route path="/system-health" element={
                            <PrivateRoute allowedRoles={['AUTHORITY', 'RESPONSE_TEAM', 'ADMIN']}>
                                <SystemHealth />
                            </PrivateRoute>
                        } />

                        <Route path="*" element={<Navigate to="/" />} />
                    </Routes>
                </div>
            </main>
        </div>
    );
}
