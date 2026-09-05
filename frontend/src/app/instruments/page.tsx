"use client";
import { useEffect, useState } from "react";
import { fetchInstruments, getToken } from "@/lib/api";

export default function InstrumentsList() {
    const [instruments, setInstruments] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!getToken()) { window.location.href = "/login"; return; }
        fetchInstruments()
            .then(setInstruments)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="p-8 text-center text-gray-400">Loading instruments...</div>;
    if (error) return <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded">{error}</div>;

    return (
        <div>
            <div className="flex justify-between items-center mb-5">
                <h1 className="text-2xl font-bold text-gray-900">Instrument Registry</h1>
                <a href="/instruments/new" className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md shadow-sm hover:bg-blue-700 transition-colors">+ Register New</a>
            </div>
            <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">ID</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Manufacturer / Model</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Serial No.</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Class</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Max Cap.</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Unit</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {instruments.map(inst => (
                            <tr key={inst.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-4 py-3 text-sm font-mono text-gray-500">{inst.instrument_id}</td>
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">{inst.manufacturer} {inst.model}</td>
                                <td className="px-4 py-3 text-sm text-gray-600 font-mono">{inst.serial_number}</td>
                                <td className="px-4 py-3"><span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">{inst.accuracy_class}</span></td>
                                <td className="px-4 py-3 text-sm text-gray-600">{inst.max_capacity}</td>
                                <td className="px-4 py-3 text-sm text-gray-600">{inst.unit}</td>
                                <td className="px-4 py-3 text-sm">
                                    <a href={`/instruments/${inst.id}`} className="text-blue-600 hover:text-blue-800 font-medium">View / Test →</a>
                                </td>
                            </tr>
                        ))}
                        {instruments.length === 0 && (
                            <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-400">No instruments registered yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
