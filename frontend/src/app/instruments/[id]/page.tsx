"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchInstrument, createTest, getToken } from "@/lib/api";

export default function InstrumentDetail() {
    const { id } = useParams();
    const router = useRouter();
    const [instrument, setInstrument] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!getToken()) { window.location.href = "/login"; return; }
        fetchInstrument(Number(id))
            .then(setInstrument)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false));
    }, [id]);

    const handleStartTest = async (testType: string) => {
        setCreating(true);
        setError("");
        try {
            const test = await createTest({ instrument_id: Number(id), test_type: testType });
            router.push(`/tests/${test.id}/execute`);
        } catch (err: any) {
            setError(err.message || "Failed to create test");
        } finally {
            setCreating(false);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-400">Loading instrument details...</div>;
    if (error && !instrument) return <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded">{error}</div>;
    if (!instrument) return null;

    const specs = [
        { label: "Instrument ID", value: instrument.instrument_id },
        { label: "Manufacturer", value: instrument.manufacturer },
        { label: "Model", value: instrument.model },
        { label: "Serial Number", value: instrument.serial_number, mono: true },
        { label: "Accuracy Class", value: instrument.accuracy_class, badge: true },
        { label: "Max Capacity", value: `${instrument.max_capacity} ${instrument.unit}` },
        { label: "Min Capacity", value: `${instrument.min_capacity} ${instrument.unit}` },
        { label: "Verification Interval (e)", value: `${instrument.verification_interval} ${instrument.unit}` },
    ];

    return (
        <div className="space-y-6">
            {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded text-sm">{error}</div>}

            <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4 border-b border-gray-100 pb-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">{instrument.manufacturer} {instrument.model}</h1>
                        <p className="text-sm text-gray-500 font-mono mt-1">S/N: {instrument.serial_number}</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <a href={`/instruments/${id}/history`} className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-blue-600 px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-sm">
                            View Full Lifecycle History
                        </a>
                    </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    {specs.map(s => (
                        <div key={s.label}>
                            <p className="text-xs text-gray-500 uppercase tracking-wider">{s.label}</p>
                            {s.badge ? (
                                <span className="inline-flex items-center mt-1 px-2 py-0.5 rounded text-sm font-semibold bg-blue-100 text-blue-800">{s.value}</span>
                            ) : (
                                <p className={`mt-1 text-sm font-medium text-gray-900 ${s.mono ? "font-mono" : ""}`}>{s.value}</p>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4">Start New Calibration</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border border-blue-200 bg-blue-50 rounded-lg p-5 flex flex-col justify-between hover:border-blue-400 transition-colors">
                        <div>
                            <h3 className="font-bold text-blue-900 text-lg">Full Calibration (OIML R-76)</h3>
                            <p className="text-sm text-blue-700 mt-2">Comprehensive suite including Accuracy, Repeatability, Eccentricity, Zero, and Tare modules.</p>
                        </div>
                        <button onClick={() => handleStartTest("Full Calibration")} disabled={creating}
                            className="mt-5 w-full text-center bg-blue-600 text-white px-4 py-2.5 rounded-md text-sm font-bold hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-sm">
                            {creating ? "Creating Session..." : "Start Calibration Session →"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
