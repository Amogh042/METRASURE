"use client";

import { useEffect, useState } from "react";
import { getToken, API_URL } from "@/lib/api";
import { 
    Activity, FileCheck2, AlertTriangle, FileText, CheckCircle2, 
    XCircle, Clock, ArrowRight, Server, Play, Search, Scale
} from "lucide-react";
import { 
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from "recharts";
import { format, formatDistanceToNow } from "date-fns";
import TourManager from "@/components/TourManager";

export default function Dashboard() {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // Filters
    const [days, setDays] = useState(30);

    useEffect(() => {
        if (!getToken()) {
            window.location.href = "/login";
            return;
        }

        (async () => {
            try {
                setLoading(true);
                const res = await fetch(`${API_URL}/dashboard/stats?days=${days}`, {
                    headers: { Authorization: `Bearer ${getToken()}` }
                });
                if (!res.ok) throw new Error("Failed to load dashboard data");
                const data = await res.json();
                setStats(data);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        })();
    }, [days]);

    if (loading) return <div className="p-8 text-center text-slate-500 font-medium">Loading Dashboard...</div>;
    if (error) return <div className="p-4 bg-red-50 text-red-700 m-6 rounded-lg font-medium">{error}</div>;

    const { overview, recent_tests, failure_analysis, attention_required } = stats;

    return (
        <div className="max-w-7xl mx-auto space-y-6" data-tour="dashboard">
            <TourManager />
            {/* Header & Global Filters */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Laboratory Overview</h1>
                    <p className="text-sm text-slate-500">Legal Metrology Activity Dashboard</p>
                </div>
                <div className="flex gap-2">
                    <select 
                        value={days} 
                        onChange={(e) => setDays(Number(e.target.value))}
                        className="bg-white border border-slate-300 text-slate-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2 font-medium shadow-sm">
                        <option value={7}>Last 7 Days</option>
                        <option value={30}>Last 30 Days</option>
                        <option value={90}>Last 90 Days</option>
                    </select>
                </div>
            </div>

            {/* Overview Metric Cards */}
            <div data-tour="dashboard-stats" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <MetricCard 
                    title="Registered Instruments" 
                    value={overview.instruments_registered} 
                    icon={<Scale className="w-5 h-5 text-indigo-600" />} 
                    trend="+12% from last month"
                />
                <MetricCard 
                    title="Tests Completed" 
                    value={overview.tests_completed} 
                    icon={<Activity className="w-5 h-5 text-blue-600" />} 
                    trend="In selected period"
                />
                <MetricCard 
                    title="Tests Passed" 
                    value={overview.tests_passed} 
                    icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />} 
                    valueClass="text-emerald-700"
                />
                <MetricCard 
                    title="Tests Failed" 
                    value={overview.tests_failed} 
                    icon={<AlertTriangle className="w-5 h-5 text-rose-600" />} 
                    valueClass="text-rose-700"
                />
                <MetricCard 
                    title="Reports Generated" 
                    value={overview.reports_generated} 
                    icon={<FileCheck2 className="w-5 h-5 text-amber-600" />} 
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Left Column: Recent Tests (Takes up 2 cols on lg) */}
                <div className="lg:col-span-2 space-y-6">
                    <div data-tour="test-results" className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                        <div className="px-5 py-4 border-b border-slate-100 flex justify-between items-center">
                            <h2 className="text-base font-bold text-slate-800">Recent Calibrations</h2>
                            <a href="/tests" className="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1">
                                View all <ArrowRight className="w-4 h-4" />
                            </a>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full text-sm">
                                <thead className="bg-slate-50 text-slate-500 font-medium">
                                    <tr>
                                        <th className="px-5 py-3 text-left">Instrument</th>
                                        <th className="px-5 py-3 text-left">Date</th>
                                        <th className="px-5 py-3 text-left">Technician</th>
                                        <th className="px-5 py-3 text-left">Result</th>
                                        <th className="px-5 py-3 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {recent_tests.length === 0 ? (
                                        <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">No recent tests found.</td></tr>
                                    ) : recent_tests.map((t: any) => (
                                        <tr key={t.id} className="hover:bg-slate-50/50 transition-colors">
                                            <td className="px-5 py-3">
                                                <p className="font-semibold text-slate-800">{t.instrument}</p>
                                                <p className="text-xs text-slate-500 font-mono mt-0.5">{t.serial_number}</p>
                                            </td>
                                            <td className="px-5 py-3 text-slate-600">
                                                {format(new Date(t.test_date), "MMM d, yyyy")}
                                            </td>
                                            <td className="px-5 py-3 text-slate-600">
                                                {t.technician}
                                            </td>
                                            <td className="px-5 py-3">
                                                <ResultBadge result={t.overall_result} />
                                            </td>
                                            <td className="px-5 py-3 text-right">
                                                <a href={`/tests/${t.id}/results`} className="text-blue-600 hover:text-blue-800 font-medium">
                                                    Summary
                                                </a>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Right Column: Charts & Attention */}
                <div className="space-y-6">
                    
                    {/* Failure Analysis Chart */}
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                        <h2 className="text-base font-bold text-slate-800 mb-4">Failure Analysis</h2>
                        <p className="text-xs text-slate-500 mb-6">Non-conformances detected per OIML R-76 module.</p>
                        
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={failure_analysis} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} allowDecimals={false} />
                                    <Tooltip 
                                        cursor={{ fill: '#f8fafc' }}
                                        contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Bar dataKey="failures" radius={[4, 4, 0, 0]}>
                                        {failure_analysis.map((entry: any, index: number) => (
                                            <Cell key={`cell-${index}`} fill={entry.failures > 0 ? '#e11d48' : '#cbd5e1'} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="bg-slate-900 rounded-xl shadow-sm border border-slate-800 p-5 text-white">
                        <h2 className="text-base font-bold mb-4">Quick Actions</h2>
                        <div className="grid grid-cols-2 gap-3">
                            <a href="/instruments/new" className="flex flex-col items-center justify-center p-3 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors text-center group">
                                <Server className="w-5 h-5 text-blue-400 mb-2 group-hover:scale-110 transition-transform" />
                                <span className="text-xs font-medium">Register<br/>Instrument</span>
                            </a>
                            <a href="/instruments" data-tour="start-test" className="flex flex-col items-center justify-center p-3 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors text-center group">
                                <Play className="w-5 h-5 text-emerald-400 mb-2 group-hover:scale-110 transition-transform" />
                                <span className="text-xs font-medium">Start<br/>Calibration</span>
                            </a>
                            <a href="/history" data-tour="reports" className="flex flex-col items-center justify-center p-3 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors text-center group">
                                <FileText className="w-5 h-5 text-amber-400 mb-2 group-hover:scale-110 transition-transform" />
                                <span className="text-xs font-medium">View<br/>Reports</span>
                            </a>
                            <a href="/history" data-tour="verification" className="flex flex-col items-center justify-center p-3 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors text-center group">
                                <Search className="w-5 h-5 text-purple-400 mb-2 group-hover:scale-110 transition-transform" />
                                <span className="text-xs font-medium">Verify<br/>QR / Certificate</span>
                            </a>
                        </div>
                    </div>

                    {/* Attention Required */}
                    <div className="bg-white rounded-xl shadow-sm border border-rose-200 overflow-hidden">
                        <div className="bg-rose-50 px-5 py-3 border-b border-rose-100 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 text-rose-600" />
                            <h2 className="text-sm font-bold text-rose-900">Requires Attention</h2>
                        </div>
                        <div className="divide-y divide-slate-100">
                            {attention_required.length === 0 ? (
                                <div className="p-5 text-center text-sm text-slate-500">All instruments are compliant.</div>
                            ) : attention_required.map((inst: any) => (
                                <div key={inst.id} className="p-4 flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-bold text-slate-800">{inst.instrument}</p>
                                        <p className="text-xs text-slate-500 font-mono mt-0.5">{inst.serial_number}</p>
                                    </div>
                                    <span className="text-xs font-bold text-rose-700 bg-rose-100 px-2.5 py-1 rounded-full">
                                        RETEST REQ.
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}

function MetricCard({ title, value, icon, trend, valueClass = "text-slate-900" }: { title: string, value: string | number, icon: React.ReactNode, trend?: string, valueClass?: string }) {
    return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between">
            <div className="flex justify-between items-start mb-4">
                <h3 className="text-sm font-semibold text-slate-600 leading-tight">{title}</h3>
                <div className="p-2 bg-slate-50 rounded-lg">{icon}</div>
            </div>
            <div>
                <p className={`text-3xl font-black tracking-tight ${valueClass}`}>{value}</p>
                {trend && <p className="text-xs text-slate-400 mt-1">{trend}</p>}
            </div>
        </div>
    );
}

function ResultBadge({ result }: { result: string }) {
    if (result === "PASS") return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200"><CheckCircle2 className="w-3.5 h-3.5"/> PASS</span>;
    if (result === "FAIL") return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200"><XCircle className="w-3.5 h-3.5"/> FAIL</span>;
    return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200"><Clock className="w-3.5 h-3.5"/> PEND</span>;
}
