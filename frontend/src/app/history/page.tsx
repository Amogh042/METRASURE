"use client";

import { useEffect, useState } from "react";
import { searchHistory, API_URL } from "@/lib/api";
import { Search, Filter, CheckCircle2, XCircle, FileText, Activity } from "lucide-react";
import { format } from "date-fns";

export default function GlobalHistoryPage() {
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    
    // Filters
    const [searchQ, setSearchQ] = useState("");
    const [accClass, setAccClass] = useState("");
    const [result, setResult] = useState("");
    const [testType, setTestType] = useState("");
    
    const loadData = async () => {
        try {
            setLoading(true);
            const data = await searchHistory({
                q: searchQ,
                accuracy_class: accClass,
                result: result,
                test_type: testType
            });
            setHistory(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    useEffect(() => {
        loadData();
    }, []);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        loadData();
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Global Audit & History</h1>
                <p className="text-sm text-slate-500">Search and filter all historical calibration records across the laboratory</p>
            </div>

            {/* Filter Bar */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
                <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4 items-end">
                    <div className="flex-1 w-full">
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Global Search</label>
                        <div className="relative">
                            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                            <input 
                                type="text"
                                placeholder="Serial number, make, model, instrument ID..."
                                value={searchQ}
                                onChange={e => setSearchQ(e.target.value)}
                                className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                    </div>
                    
                    <div className="w-full md:w-48">
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Accuracy Class</label>
                        <select 
                            value={accClass}
                            onChange={e => setAccClass(e.target.value)}
                            className="w-full border border-slate-300 rounded-lg text-sm px-3 py-2 bg-white"
                        >
                            <option value="">All Classes</option>
                            <option value="I">Class I</option>
                            <option value="II">Class II</option>
                            <option value="III">Class III</option>
                            <option value="IIII">Class IIII</option>
                        </select>
                    </div>

                    <div className="w-full md:w-48">
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Result</label>
                        <select 
                            value={result}
                            onChange={e => setResult(e.target.value)}
                            className="w-full border border-slate-300 rounded-lg text-sm px-3 py-2 bg-white"
                        >
                            <option value="">All Results</option>
                            <option value="PASS">PASS</option>
                            <option value="FAIL">FAIL</option>
                        </select>
                    </div>

                    <div className="w-full md:w-auto">
                        <button type="submit" className="w-full md:w-auto bg-blue-600 text-white text-sm font-semibold px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
                            <Filter className="w-4 h-4" /> Apply Filters
                        </button>
                    </div>
                </form>
            </div>

            {/* Results Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                        <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                            <tr>
                                <th className="px-6 py-4 text-left">Date</th>
                                <th className="px-6 py-4 text-left">Instrument</th>
                                <th className="px-6 py-4 text-left">Test ID</th>
                                <th className="px-6 py-4 text-left">Result</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 bg-white">
                            {loading ? (
                                <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-400">Searching records...</td></tr>
                            ) : history.length === 0 ? (
                                <tr><td colSpan={5} className="px-6 py-12 text-center text-slate-400">No matching records found.</td></tr>
                            ) : history.map((t: any) => (
                                <tr key={t.test_id} className="hover:bg-slate-50/70 transition-colors">
                                    <td className="px-6 py-4 text-slate-700 font-medium">
                                        {format(new Date(t.test_date), "MMM d, yyyy")}
                                    </td>
                                    <td className="px-6 py-4">
                                        <p className="font-bold text-slate-800">{t.instrument.manufacturer} {t.instrument.model}</p>
                                        <p className="text-xs font-mono text-slate-500 mt-0.5">S/N: {t.instrument.serial_number} | Class {t.instrument.accuracy_class}</p>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="font-mono text-slate-600 bg-slate-100 px-2 py-1 rounded text-xs">{t.test_number.substring(0, 15)}...</span>
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
                                    <td className="px-6 py-4 text-right space-x-3 whitespace-nowrap">
                                        <a href={`/instruments/${t.instrument.id}/history`} className="text-slate-500 hover:text-blue-600 transition-colors font-medium text-xs border border-slate-200 px-2 py-1 rounded bg-white shadow-sm">
                                            Inst. History
                                        </a>
                                        <a href={`/tests/${t.test_id}/history-detail`} className="text-blue-600 hover:text-blue-800 transition-colors font-semibold">
                                            Audit Details
                                        </a>
                                        {t.report_id && (
                                            <button 
                                                onClick={() => window.open(`${API_URL}/reports/${t.report_id}/download`, "_blank")}
                                                className="text-slate-500 hover:text-slate-900 transition-colors ml-2"
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
