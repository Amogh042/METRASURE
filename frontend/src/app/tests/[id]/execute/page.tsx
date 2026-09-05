"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    fetchTest, fetchInstrument, fetchMeasurements,
    addMeasurement, deleteMeasurement, calculateTest, getToken
} from "@/lib/api";

const MODULES = ["Accuracy", "Repeatability", "Eccentricity", "Zero", "Tare"];

interface MeasRow {
    id?: number;
    sequence: number;
    test_load: string;
    indicated_value: string;
    position?: string;
    saved: boolean;
}

export default function TestSession() {
    const { id } = useParams();
    const router = useRouter();
    const testId = Number(id);

    const [test, setTest] = useState<any>(null);
    const [instrument, setInstrument] = useState<any>(null);
    const [activeModule, setActiveModule] = useState("Accuracy");
    
    // Module State
    const [rows, setRows] = useState<MeasRow[]>([]);
    const [result, setResult] = useState<any>(null);
    const [whyIdx, setWhyIdx] = useState<number | null>(null);

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [calculating, setCalculating] = useState(false);
    const [error, setError] = useState("");

    // Load active module data
    const loadModuleData = useCallback(async (moduleName: string) => {
        try {
            setLoading(true);
            const meas = await fetchMeasurements(testId, moduleName);
            if (meas.length > 0) {
                setRows(meas.map((m: any) => ({
                    id: m.id,
                    sequence: m.sequence,
                    test_load: String(m.test_load),
                    indicated_value: String(m.indicated_value),
                    position: m.position || "",
                    saved: true,
                })));
                
                // Try to load calculation results if they exist...
                // (Backend doesn't have a GET /results route yet, so we just reset result to null 
                // and force user to click calculate again if they revisit the tab, or we can wait for the subagent).
                setResult(null); 
            } else {
                setRows([{ sequence: 1, test_load: "", indicated_value: "", position: "", saved: false }]);
                setResult(null);
            }
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
            setWhyIdx(null);
        }
    }, [testId]);

    // Initial Test load
    useEffect(() => {
        if (!getToken()) { window.location.href = "/login"; return; }
        (async () => {
            try {
                const t = await fetchTest(testId);
                setTest(t);
                const inst = await fetchInstrument(t.instrument_id);
                setInstrument(inst);
                await loadModuleData(activeModule);
            } catch (e: any) {
                setError(e.message);
            }
        })();
    }, [testId, activeModule, loadModuleData]);

    // --- Row operations ---
    const addRow = () => {
        setRows(prev => [...prev, { sequence: prev.length + 1, test_load: "", indicated_value: "", position: "", saved: false }]);
        setResult(null);
    };

    const removeRow = async (idx: number) => {
        const row = rows[idx];
        if (row.saved && row.id) {
            try { await deleteMeasurement(testId, row.id); } catch {}
        }
        setRows(prev => {
            const next = prev.filter((_, i) => i !== idx);
            return next.map((r, i) => ({ ...r, sequence: i + 1 }));
        });
        setResult(null);
    };

    const updateRow = (idx: number, field: keyof MeasRow, value: string) => {
        setRows(prev => prev.map((r, i) => i === idx ? { ...r, [field]: value, saved: false } : r));
        setResult(null);
    };

    // --- Save ---
    const handleSave = async () => {
        setError("");
        for (let i = 0; i < rows.length; i++) {
            const isZero = activeModule === "Zero";
            if ((!isZero && !rows[i].test_load) || !rows[i].indicated_value) {
                setError(`Row ${i + 1}: ${isZero ? "Indicated Value is" : "Test Load and Indicated Value are"} required.`);
                return;
            }
            if (activeModule === "Eccentricity" && !rows[i].position) {
                setError(`Row ${i + 1}: Position is required for Eccentricity test.`);
                return;
            }
        }

        setSaving(true);
        try {
            // Delete all existing measurements for this module first to avoid duplicates
            // We use the 'id' field to determine if it was previously saved to DB
            const existing = rows.filter(r => r.id);
            for (const r of existing) { await deleteMeasurement(testId, r.id!); }

            const newRows: MeasRow[] = [];
            for (let i = 0; i < rows.length; i++) {
                const r = rows[i];
                const saved = await addMeasurement(testId, {
                    test_module: activeModule,
                    sequence: i + 1,
                    test_load: activeModule === "Zero" ? 0 : parseFloat(r.test_load),
                    indicated_value: parseFloat(r.indicated_value),
                    position: r.position || null,
                    unit: instrument.unit,
                });
                newRows.push({ id: saved.id, sequence: i + 1, test_load: r.test_load, indicated_value: r.indicated_value, position: r.position, saved: true });
            }
            setRows(newRows);
        } catch (err: any) {
            setError(err.message || "Failed to save");
        } finally {
            setSaving(false);
        }
    };

    // --- Calculate ---
    const handleCalculate = async () => {
        setError("");
        const unsaved = rows.some(r => !r.saved);
        if (unsaved) await handleSave();

        setCalculating(true);
        try {
            const res = await calculateTest(testId, activeModule);
            setResult(res);
        } catch (err: any) {
            setError(err.message || "Calculation failed");
        } finally {
            setCalculating(false);
        }
    };

    // --- Render Module Columns ---
    const renderColumns = () => {
        const isEccentricity = activeModule === "Eccentricity";
        const loadLabel = activeModule === "Tare" ? `Net Load (${instrument?.unit})` : `Test Load (${instrument?.unit})`;
        
        return (
            <thead className="bg-gray-50">
                <tr>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase w-12">#</th>
                    {isEccentricity && <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase">Position</th>}
                    {activeModule !== "Zero" && <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase">{loadLabel}</th>}
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase">Indicated Value ({instrument?.unit})</th>
                    {result && <>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase">Error</th>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase">MPE Limit</th>
                        <th className="px-4 py-2.5 text-center text-xs font-semibold text-gray-500 uppercase">Result</th>
                        <th className="px-4 py-2.5 text-center text-xs font-semibold text-gray-500 uppercase w-16"></th>
                    </>}
                    <th className="px-4 py-2.5 w-12"></th>
                </tr>
            </thead>
        );
    };

    const renderRowCells = (row: MeasRow, idx: number, resRow: any, isFail: boolean) => {
        const isEccentricity = activeModule === "Eccentricity";
        const isRepeat = activeModule === "Repeatability";
        const isZero = activeModule === "Zero";

        // In repeatability, the result is module-wide, not per-measurement.
        const showPerRowResult = result && !isRepeat;

        return (
            <>
                <td className="px-4 py-2 text-sm text-gray-400 font-mono">{idx + 1}</td>
                {isEccentricity && (
                    <td className="px-4 py-2">
                        <select value={row.position} onChange={e => updateRow(idx, "position", e.target.value)}
                            className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:ring-blue-500">
                            <option value="">Select...</option>
                            <option value="Center">Center</option>
                            <option value="Front-Left">Front-Left</option>
                            <option value="Front-Right">Front-Right</option>
                            <option value="Back-Left">Back-Left</option>
                            <option value="Back-Right">Back-Right</option>
                        </select>
                    </td>
                )}
                {!isZero && (
                    <td className="px-4 py-2">
                        <input type="number" step="any" min="0" value={row.test_load} onChange={e => updateRow(idx, "test_load", e.target.value)}
                            className="w-full rounded border border-gray-200 px-2 py-1.5 text-sm focus:ring-blue-500" placeholder="0.00" />
                    </td>
                )}
                <td className="px-4 py-2">
                    <input type="number" step="any" value={row.indicated_value} onChange={e => updateRow(idx, "indicated_value", e.target.value)}
                        className={`w-full rounded border px-2 py-1.5 text-sm ${isFail ? "border-red-300 bg-red-50" : "border-gray-200"} focus:ring-blue-500`} placeholder="0.00" />
                </td>
                
                {showPerRowResult && resRow && <>
                    <td className={`px-4 py-2 text-sm font-mono font-medium ${isFail ? "text-red-700" : "text-gray-700"}`}>
                        {resRow.error >= 0 ? "+" : ""}{resRow.error.toFixed(4)}
                    </td>
                    <td className="px-4 py-2 text-sm font-mono text-gray-500">±{resRow.mpe_limit.toFixed(4)}</td>
                    <td className="px-4 py-2 text-center">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${resRow.passed ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                            {resRow.passed ? "PASS" : "FAIL"}
                        </span>
                    </td>
                    <td className="px-4 py-2 text-center">
                        {!resRow.passed && (
                            <button onClick={() => setWhyIdx(whyIdx === idx ? null : idx)} className="text-xs text-red-600 hover:text-red-800 underline">Why?</button>
                        )}
                    </td>
                </>}
                {showPerRowResult && !resRow && <td colSpan={4}></td>}
                {/* Repeatability empty cells to align layout since no per-row result */}
                {result && isRepeat && <td colSpan={4} className="text-center text-xs text-gray-400">See overall</td>}
                
                <td className="px-4 py-2 text-center">
                    {rows.length > 1 && (
                        <button onClick={() => removeRow(idx)} className="text-gray-300 hover:text-red-500">×</button>
                    )}
                </td>
            </>
        );
    };

    if (!test || !instrument) return <div className="p-8 text-center text-gray-400">Loading session...</div>;

    const hasUnsaved = rows.some(r => !r.saved);
    const allEmpty = rows.every(r => (!r.test_load && activeModule !== "Zero") && !r.indicated_value);

    return (
        <div className="flex flex-col md:flex-row gap-6">
            {/* Sidebar Navigation */}
            <div className="w-full md:w-64 flex-shrink-0">
                <div className="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden sticky top-6">
                    <div className="p-4 bg-slate-50 border-b border-gray-200">
                        <h2 className="font-bold text-slate-800 text-lg">Test Session</h2>
                        <p className="text-xs text-slate-500 mt-1">ID: {test.test_number}</p>
                    </div>
                    <nav className="flex flex-col">
                        {MODULES.map(mod => (
                            <button key={mod} onClick={() => { setActiveModule(mod); setResult(null); }}
                                className={`text-left px-5 py-3 text-sm font-medium border-l-4 transition-colors ${
                                    activeModule === mod 
                                    ? "bg-blue-50 border-blue-600 text-blue-800" 
                                    : "border-transparent text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                                }`}>
                                {mod} Test
                            </button>
                        ))}
                    </nav>
                    <div className="p-4 bg-slate-50 border-t border-gray-200">
                        <button onClick={() => router.push(`/tests/${testId}/results`)}
                            className="w-full bg-slate-800 text-white text-sm font-bold py-2 rounded shadow-sm hover:bg-slate-900 transition-colors">
                            View Full Summary
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 space-y-5">
                <div className="bg-white shadow-sm border border-gray-200 rounded-lg p-5">
                    <h1 className="text-2xl font-bold text-gray-900">{activeModule} Module</h1>
                    <p className="text-sm text-gray-500 mt-1">
                        {activeModule === "Accuracy" && "Error of indication across multiple test loads."}
                        {activeModule === "Repeatability" && "Difference between repeated weighings of the same load."}
                        {activeModule === "Eccentricity" && "Indications for different positions of a single load."}
                        {activeModule === "Zero" && "Effect of zero deviation after zero-setting."}
                        {activeModule === "Tare" && "Accuracy of net loads using tare functionality."}
                    </p>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm flex items-center justify-between">
                        <span>{error}</span>
                        <button onClick={() => setError("")} className="text-red-400">✕</button>
                    </div>
                )}

                {/* Measurement Table */}
                <div className="bg-white shadow-sm border border-gray-200 rounded-lg">
                    <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                        <h2 className="text-sm font-semibold text-gray-700 uppercase">Data Entry</h2>
                        <div className="flex gap-2">
                            <button onClick={addRow} className="px-3 py-1.5 text-xs font-medium bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-700">+ Add Row</button>
                        </div>
                    </div>
                    {loading ? (
                        <div className="p-8 text-center text-gray-400 text-sm">Loading module...</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full">
                                {renderColumns()}
                                <tbody className="divide-y divide-gray-100">
                                    {rows.map((row, idx) => {
                                        const resRow = activeModule === "Eccentricity" 
                                            ? result?.calculated_values?.positions?.find((m: any) => m.position === row.position && m.load === parseFloat(row.test_load))
                                            : result?.calculated_values?.measurements?.find((m: any) => m.sequence === idx + 1);
                                        const isFail = resRow && !resRow.passed;
                                        return (
                                            <tr key={idx} className={isFail ? "bg-red-50" : "hover:bg-gray-50"}>
                                                {renderRowCells(row, idx, resRow, isFail)}
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                    
                    {/* Why Explanation for per-row fails */}
                    {whyIdx !== null && result && activeModule !== "Repeatability" && (() => {
                        const row = rows[whyIdx];
                        const resRow = activeModule === "Eccentricity"
                            ? result.calculated_values.positions.find((m: any) => m.position === row.position && m.load === parseFloat(row.test_load))
                            : result.calculated_values.measurements.find((m: any) => m.sequence === whyIdx + 1);
                        if (!resRow || resRow.passed) return null;
                        return (
                            <div className="mx-5 mb-4 mt-2 bg-red-50 border border-red-200 rounded p-4 text-sm">
                                <p className="font-semibold text-red-800 mb-1">Explanation for Row {whyIdx + 1}</p>
                                <p className="text-red-700">Calculated error = {resRow.error >= 0 ? "+" : ""}{resRow.error.toFixed(4)} {instrument.unit}.</p>
                                <p className="text-red-700">MPE Limit = ±{resRow.mpe_limit.toFixed(4)} {instrument.unit}.</p>
                                <p className="text-red-700 mt-1">Because |{Math.abs(resRow.error).toFixed(4)}| &gt; {resRow.mpe_limit.toFixed(4)}, it <strong>fails</strong> the rule.</p>
                            </div>
                        );
                    })()}

                    {/* Actions */}
                    <div className="px-5 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50 rounded-b-lg">
                        <div className="text-xs text-gray-400">
                            {rows.length} row{rows.length !== 1 ? "s" : ""}{hasUnsaved ? " · Unsaved" : ""}
                        </div>
                        <div className="flex gap-2">
                            <button onClick={handleSave} disabled={saving || allEmpty}
                                className="px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded hover:bg-gray-50 text-gray-700 disabled:opacity-40">
                                {saving ? "Saving..." : "Save Data"}
                            </button>
                            <button onClick={handleCalculate} disabled={calculating || allEmpty}
                                className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-40 shadow-sm">
                                {calculating ? "Calculating..." : "Calculate Module"}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Repeatability specific result or overall result */}
                {result && (
                    <div className={`rounded-lg border-2 p-6 shadow-sm ${result.pass_fail === "PASS" ? "bg-green-50 border-green-300" : "bg-red-50 border-red-300"}`}>
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-bold">{result.pass_fail === "PASS" ? "✓ MODULE PASSED" : "✗ MODULE FAILED"}</h3>
                                <p className="text-sm mt-1 text-gray-800 font-medium">{result.explanation}</p>
                                {activeModule === "Repeatability" && result.calculated_values && (
                                    <div className="mt-3 text-sm text-gray-700 space-y-1 bg-white/60 p-3 rounded">
                                        <p>Max Indication: <span className="font-mono font-bold">{result.calculated_values.max_indication ?? "—"}</span></p>
                                        <p>Min Indication: <span className="font-mono font-bold">{result.calculated_values.min_indication ?? "—"}</span></p>
                                        <p>Max Difference: <span className="font-mono font-bold">{result.calculated_values.max_difference != null ? result.calculated_values.max_difference.toFixed(4) : "—"}</span></p>
                                        <p>MPE Limit: <span className="font-mono font-bold">{result.calculated_values.mpe_limit != null ? result.calculated_values.mpe_limit.toFixed(4) : "—"}</span></p>
                                    </div>
                                )}
                                <p className="text-xs mt-3 text-gray-500">Rule Engine: {result.applicable_rule} · Source: {result.source_reference}</p>
                            </div>
                            <span className={`text-4xl font-black ${result.pass_fail === "PASS" ? "text-green-600" : "text-red-600"}`}>
                                {result.pass_fail}
                            </span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
