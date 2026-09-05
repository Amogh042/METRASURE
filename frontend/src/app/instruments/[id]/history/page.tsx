"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getInstrumentHistoryStats, searchHistory, API_URL, generateReport } from "@/lib/api";
import { Scale, CheckCircle2, XCircle, AlertTriangle, FileText, Download, Calendar, Activity, ChevronRight, Search } from "lucide-react";
import { format } from "date-fns";

export default function InstrumentHistoryPage() {
    const { id } = useParams();
    const instId = Number(id);
    
    const [stats, setStats] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    
    const [searchQ, setSearchQ] = useState("");
    const [filterResult, setFilterResult] = useState("");
    
    const loadData = async () => {
        try {
            setLoading(true);
            const [statsRes, historyRes] = await Promise.all([
                getInstrumentHistoryStats(instId),
                searchHistory({ instrument_id: instId, q: searchQ, result: filterResult })
            ]);
            setStats(statsRes);
            setHistory(historyRes);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    useEffect(() => {
        loadData();
    }, [instId, filterResult]); // re-run if filter changes

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        loadData();
    };

    if (loading && !stats) return <div className="p-8 text-center text-slate-500 font-medium">Loading instrument history...</div>;
    if (error) return <div className="p-4 bg-red-50 text-red-700 m-6 rounded-lg font-medium">{error}</div>;
    if (!stats) return null;

    const { instrument, stats: instStats } = stats;

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex items-center gap-2 text-sm text-slate-500 mb-2">
                <a href="/instruments" className="hover:text-blue-600 font-medium">Registry</a>
                <ChevronRight className="w-4 h-4" />
                <a href={`/instruments/${instId}`} className="hover:text-blue-600 font-medium">{instrument.instrument_id}</a>
                <ChevronRight className="w-4 h-4" />
                <span className="text-slate-800 font-bold">History</span>
            </div>

            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Instrument Lifecycle</h1>
                    <p className="text-sm text-slate-500">Comprehensive history and compliance log</p>
                </div>
                <a href={`/instruments/${instId}`} className="bg-white border border-slate-300 text-slate-700 font-semibold py-2 px-4 rounded-lg hover:bg-slate-50 shadow-sm text-sm">
                    View Instrument Details
                </a>
            </div>

            {/* Overview Panel */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col md:flex-row gap-8">
                
                <div className="flex-1 border-b md:border-b-0 md:border-r border-slate-200 pb-6 md:pb-0 md:pr-6">
                    <div className="flex items-start gap-4">
                        <div className="bg-blue-50 text-blue-600 p-3 rounded-xl">
                            <Scale className="w-8 h-8" />
                        </div>
                        <div>
                            <h2 className="text-xl font-black text-slate-900">{instrument.manufacturer} {instrument.model}</h2>
                            <div className="text-sm text-slate-500 font-mono mt-1 space-y-0.5">
                                <p>S/N: <span className="font-semibold text-slate-700">{instrument.serial_number}</span></p>
                                <p>ID: <span className="font-semibold text-slate-700">{instrument.instrument_id}</span></p>
                                <p>Class: <span className="font-semibold text-slate-700 bg-slate-100 px-1.5 rounded">{instrument.accuracy_class}</span></p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex-1 grid grid-cols-2 gap-4">
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Total Calibrations</p>
                        <p className="text-2xl font-black text-slate-900">{instStats.total_tests}</p>
                    </div>
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Last Calibration</p>
                        <p className="text-sm font-bold text-slate-900 mt-1">
                            {instStats.last_test_date ? format(new Date(instStats.last_test_date), "MMM d, yyyy") : "Never"}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Pass Count</p>
                        <p className="text-2xl font-black text-emerald-600 flex items-center gap-2">
                            {instStats.pass_count}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Fail Count</p>
                        <p className="text-2xl font-black text-rose-600 flex items-center gap-2">
                            {instStats.fail_count}
                        </p>
                    </div>
                </div>
            </div>

            {/* History Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="px-6 py-5 border-b border-slate-100 bg-slate-50 flex flex-col md:flex-row justify-between items-center gap-4">
                    <h3 className="font-bold text-slate-800 text-lg flex items-center gap-2"><Activity className="w-5 h-5 text-slate-400" /> Chronological History</h3>
                    
                    {/* Inline Filters */}
                    <form onSubmit={handleSearch} className="flex flex-wrap gap-3">
                        <div className="relative">
                            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                            <input 
                                type="text"
                                placeholder="Search tests..."
                                value={searchQ}
                                onChange={e => setSearchQ(e.target.value)}
                                className="pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm w-48 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                        <select 
                            value={filterResult}
                            onChange={e => setFilterResult(e.target.value)}
                            className="border border-slate-300 rounded-lg text-sm px-3 py-2 text-slate-700 bg-white"
                        >
                            <option value="">All Results</option>
                            <option value="PASS">PASS</option>
                            <option value="FAIL">FAIL</option>
                        </select>
                        <button type="submit" className="bg-slate-900 text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors">
                            Filter
                        </button>
                    </form>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                        <thead className="bg-white text-slate-500 font-semibold border-b border-slate-200">
                            <tr>
                                <th className="px-6 py-4 text-left">Date</th>
                                <th className="px-6 py-4 text-left">Test ID</th>
                                <th className="px-6 py-4 text-left">Test Type</th>
                                <th className="px-6 py-4 text-left">Technician</th>
                                <th className="px-6 py-4 text-left">Result</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 bg-white">
                            {history.length === 0 ? (
                                <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-400">No calibration history found.</td></tr>
                            ) : history.map((t: any) => (
                                <tr key={t.test_id} className="hover:bg-slate-50/70 transition-colors">
                                    <td className="px-6 py-4 text-slate-700 font-medium">
                                        {format(new Date(t.test_date), "MMM d, yyyy")}
                                        <div className="text-xs text-slate-400 font-normal">{format(new Date(t.test_date), "HH:mm")}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="font-mono text-slate-600 bg-slate-100 px-2 py-1 rounded text-xs">{t.test_number.substring(0, 15)}...</span>
                                    </td>
                                    <td className="px-6 py-4 text-slate-600 font-medium">
                                        {t.test_type}
                                    </td>
                                    <td className="px-6 py-4 text-slate-600">
                                        {t.technician}
                                    </td>
                                    <td className="px-6 py-4">
                                        {t.overall_result === "PASS" ? (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200"><CheckCircle2 className="w-3.5 h-3.5"/> PASS</span>
                                        ) : t.overall_result === "FAIL" ? (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200"><XCircle className="w-3.5 h-3.5"/> FAIL</span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">PENDING</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-right space-x-3">
                                        <a href={`/tests/${t.test_id}/history-detail`} className="text-blue-600 font-semibold hover:text-blue-800 transition-colors">
                                            View Audit Details
                                        </a>
                                        {t.report_id && (
                                            <button 
                                                onClick={() => window.open(`${API_URL}/reports/${t.report_id}/download`, "_blank")}
                                                className="text-slate-500 hover:text-slate-900 transition-colors"
                                                title="Download PDF"
                                            >
                                                <FileText className="w-4 h-4 inline" />
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
