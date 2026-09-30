"use client";
import { useEffect, useState } from "react";
import { fetchTests, fetchInstruments, getToken } from "@/lib/api";

export default function TestsList() {
    const [tests, setTests] = useState<any[]>([]);
    const [instruments, setInstruments] = useState<Record<number, any>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!getToken()) { window.location.href = "/login"; return; }
        Promise.all([fetchTests(), fetchInstruments()])
            .then(([testData, instData]) => {
                setTests([...testData].sort((a, b) => new Date(b.test_date).getTime() - new Date(a.test_date).getTime()));
                setInstruments(Object.fromEntries(instData.map((i: any) => [i.id, i])));
            })
            .catch(e => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="p-8 text-center text-gray-400">Loading tests...</div>;
    if (error) return <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded">{error}</div>;

    const resultBadge = (result: string | null) => {
        if (result === "PASS") return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800">PASS</span>;
        if (result === "FAIL") return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800">FAIL</span>;
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">PENDING</span>;
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-5">
                <h1 className="text-2xl font-bold text-gray-900">Tests</h1>
                <a href="/instruments" className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md shadow-sm hover:bg-blue-700 transition-colors">+ New Test</a>
            </div>
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Test No.</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Instrument</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Result</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {tests.map(t => {
                            const inst = instruments[t.instrument_id];
                            return (
                                <tr key={t.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-4 py-3 text-sm font-mono text-gray-500">{t.test_number}</td>
                                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                        {inst ? `${inst.instrument_id} · ${inst.manufacturer} ${inst.model}` : `#${t.instrument_id}`}
                                    </td>
                                    <td className="px-4 py-3 text-sm text-gray-600">{new Date(t.test_date).toLocaleDateString()}</td>
                                    <td className="px-4 py-3">{resultBadge(t.overall_result)}</td>
                                    <td className="px-4 py-3 text-sm">
                                        <a href={`/tests/${t.id}/results`} className="text-blue-600 hover:text-blue-800 font-medium">View Results →</a>
                                    </td>
                                </tr>
                            );
                        })}
                        {tests.length === 0 && (
                            <tr><td colSpan={5} className="px-4 py-8 text-center text-sm text-gray-400">No tests yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
