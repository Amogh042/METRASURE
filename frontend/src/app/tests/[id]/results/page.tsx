"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchTest, fetchInstrument, getToken, API_URL, generateReport } from "@/lib/api";

const REQUIRED_MODULES = ["Accuracy", "Repeatability", "Eccentricity", "Zero", "Tare"];

export default function TestSummary() {
    const { id } = useParams();
    const router = useRouter();
    const testId = Number(id);

    const [test, setTest] = useState<any>(null);
    const [instrument, setInstrument] = useState<any>(null);
    const [testResults, setTestResults] = useState<any[]>([]);
    
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const loadData = useCallback(async () => {
        try {
            const t = await fetchTest(testId);
            setTest(t);
            const inst = await fetchInstrument(t.instrument_id);
            setInstrument(inst);
            
            // Fetch all test results across all modules
            const token = getToken();
            const res = await fetch(`${API_URL}/tests/${testId}/results`, { 
                headers: token ? { Authorization: `Bearer ${token}` } : {} 
            });
            if (!res.ok) throw new Error("Failed to fetch test results");
            const results = await res.json();
            setTestResults(results);

        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [testId]);

    useEffect(() => {
        if (!getToken()) { window.location.href = "/login"; return; }
        loadData();
    }, [loadData]);

    if (loading) return <div className="p-8 text-center text-gray-400">Loading summary...</div>;
    if (error && !test) return <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded">{error}</div>;

    // Process results by module
    const moduleStatus: Record<string, { status: "PASS" | "FAIL" | "PENDING", details: any[] }> = {};
    
    for (const mod of REQUIRED_MODULES) {
        const modResults = testResults.filter(r => r.test_module === mod);
        
        if (modResults.length === 0) {
            moduleStatus[mod] = { status: "PENDING", details: [] };
        } else {
            // A module passes only if ALL of its result records passed
            const isFail = modResults.some(r => r.result === "FAIL");
            moduleStatus[mod] = { 
                status: isFail ? "FAIL" : "PASS",
                details: modResults
            };
        }
    }

    // Overall Status Logic
    // If any required module is PENDING or FAIL, the overall test cannot be PASS.
    const anyPending = REQUIRED_MODULES.some(m => moduleStatus[m].status === "PENDING");
    const anyFail = REQUIRED_MODULES.some(m => moduleStatus[m].status === "FAIL");
    
    let overallStatus = "PENDING";
    let statusText = "Incomplete — Finish all required modules.";
    if (anyFail) {
        overallStatus = "FAIL";
        statusText = "Test Failed — One or more modules do not meet OIML R-76 MPE limits.";
    } else if (!anyPending && !anyFail) {
        overallStatus = "PASS";
        statusText = "Test Passed — Instrument conforms to OIML R-76 rules.";
    }

    const handleGenerateReport = async () => {
        try {
            const report = await generateReport(testId);
            if (report && report.id) {
                window.open(`${API_URL}/reports/${report.id}/download`, "_blank");
            }
        } catch (err: any) {
            alert("Failed to generate report: " + err.message);
        }
    };

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
            {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded text-sm">{error}</div>}

            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Calibration Summary</h1>
                    <p className="text-sm text-gray-500 mt-0.5">Test #{test?.test_number}</p>
                </div>
                <button onClick={() => router.push(`/tests/${testId}/execute`)}
                    className="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-700 shadow-sm transition-colors">
                    ← Resume Testing
                </button>
            </div>

            {/* Overall Verdict Card */}
            <div className={`rounded-xl border-2 p-6 shadow-sm ${
                overallStatus === "PASS" ? "bg-green-50 border-green-400" :
                overallStatus === "FAIL" ? "bg-red-50 border-red-400" :
                "bg-amber-50 border-amber-300"
            }`}>
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                    <div>
                        <h2 className="text-xs uppercase tracking-widest font-bold text-gray-500 mb-1">Overall Final Verdict</h2>
                        <h3 className={`text-2xl font-black ${
                            overallStatus === "PASS" ? "text-green-700" :
                            overallStatus === "FAIL" ? "text-red-700" :
                            "text-amber-700"
                        }`}>
                            {overallStatus === "PASS" ? "✓ CERTIFIED: PASS" : 
                             overallStatus === "FAIL" ? "✗ REJECTED: FAIL" : 
                             "⏳ PENDING CALIBRATION"}
                        </h3>
                        <p className="text-sm font-medium mt-1 text-gray-700">{statusText}</p>
                    </div>
                    {overallStatus !== "PENDING" && (
                        <button onClick={handleGenerateReport}
                            className={`px-5 py-3 rounded-lg text-sm font-bold text-white shadow transition-all ${
                                overallStatus === "PASS" 
                                ? "bg-green-600 hover:bg-green-700" 
                                : "bg-red-600 hover:bg-red-700"
                            }`}>
                            Generate Official PDF Report
                        </button>
                    )}
                </div>
            </div>

            {/* Instrument Info Summary */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div><p className="text-xs text-gray-400">Manufacturer / Model</p><p className="font-medium text-sm">{instrument?.manufacturer} {instrument?.model}</p></div>
                <div><p className="text-xs text-gray-400">Serial Number</p><p className="font-medium text-sm font-mono">{instrument?.serial_number}</p></div>
                <div><p className="text-xs text-gray-400">Class</p><p className="font-medium text-sm">Class {instrument?.accuracy_class}</p></div>
                <div><p className="text-xs text-gray-400">Verification Interval (e)</p><p className="font-medium text-sm font-mono">{instrument?.verification_interval} {instrument?.unit}</p></div>
            </div>

            {/* Module Breakdowns */}
            <h2 className="text-lg font-bold text-gray-900 mt-8 mb-4">Module Breakdown</h2>
            <div className="grid grid-cols-1 gap-4">
                {REQUIRED_MODULES.map(mod => {
                    const st = moduleStatus[mod];
                    return (
                        <div key={mod} className={`rounded-lg border p-5 flex flex-col md:flex-row items-center justify-between gap-4 transition-colors ${
                            st.status === "PASS" ? "border-green-200 bg-white" :
                            st.status === "FAIL" ? "border-red-300 bg-red-50" :
                            "border-gray-200 bg-gray-50 opacity-75"
                        }`}>
                            <div className="flex-1">
                                <h3 className="font-bold text-gray-900 text-lg">{mod} Test</h3>
                                <p className="text-xs text-gray-500 mt-1">
                                    {st.status === "PENDING" ? "No calculations recorded yet." : 
                                    `${st.details.length} measurement result(s) recorded.`}
                                </p>
                                
                                {st.status === "FAIL" && (
                                    <div className="mt-3 space-y-1">
                                        {st.details.filter(d => d.result === "FAIL").map((failRow, i) => (
                                            <p key={i} className="text-xs text-red-700 bg-red-100 rounded px-2 py-1">
                                                <span className="font-bold mr-2">!</span>
                                                Error: {failRow.calculated_error >= 0 ? "+" : ""}{failRow.calculated_error} (MPE: ±{failRow.permissible_error})
                                            </p>
                                        ))}
                                    </div>
                                )}
                            </div>
                            
                            <div className="flex flex-col items-end">
                                <span className={`px-4 py-1.5 rounded-full text-sm font-black border ${
                                    st.status === "PASS" ? "bg-green-100 text-green-700 border-green-200" :
                                    st.status === "FAIL" ? "bg-red-100 text-red-700 border-red-200" :
                                    "bg-gray-200 text-gray-600 border-gray-300"
                                }`}>
                                    {st.status}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
