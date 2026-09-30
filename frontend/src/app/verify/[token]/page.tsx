"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { verifyReport, API_URL } from "@/lib/api";
import { CheckCircle, AlertTriangle, ShieldCheck, Download, Calendar, Scale, FileText } from "lucide-react";
import { format } from "date-fns";

export default function VerificationPage() {
    const { token } = useParams();
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        (async () => {
            try {
                const res = await verifyReport(token as string);
                setData(res);
            } catch (err: any) {
                setError(err.message || "Invalid or expired token");
            } finally {
                setLoading(false);
            }
        })();
    }, [token]);

    if (loading) {
        return <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-500">Verifying Report...</div>;
    }

    if (error || !data) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
                <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full text-center border border-rose-100">
                    <AlertTriangle className="w-16 h-16 text-rose-500 mx-auto mb-4" />
                    <h1 className="text-2xl font-bold text-slate-900 mb-2">Verification Failed</h1>
                    <p className="text-slate-500">{error || "The requested test report could not be verified in our system."}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-start sm:justify-center px-0 py-4 sm:p-6">
            <div className="bg-white rounded-2xl shadow-xl max-w-xl w-full min-w-0 border border-slate-200 overflow-hidden">
                
                {/* Header Header */}
                <div className="bg-emerald-600 px-5 py-8 sm:px-8 sm:py-10 text-center text-white relative overflow-hidden">
                    <div className="absolute top-0 right-0 opacity-10 transform translate-x-4 -translate-y-4">
                        <ShieldCheck className="w-48 h-48" />
                    </div>
                    <ShieldCheck className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 relative z-10" />
                    <h1 className="text-2xl sm:text-3xl font-black relative z-10">Officially Verified</h1>
                    <p className="text-emerald-100 mt-2 font-medium relative z-10">MetraSure Calibration System</p>
                </div>

                <div className="px-4 py-5 sm:px-8 sm:py-6 space-y-5 sm:space-y-6">
                    {/* Critical Information Panel */}
                    <div className="bg-slate-50 rounded-xl p-4 sm:p-5 border border-slate-200">
                        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3 mb-4">
                            <div className="min-w-0">
                                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Report Number</p>
                                <p className="text-base sm:text-lg font-mono font-bold text-slate-900 mt-1 break-all">{data.report_number}</p>
                            </div>
                            <div className="sm:text-right shrink-0">
                                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Final Verdict</p>
                                <p className={`text-xl font-black mt-1 ${data.final_result === "PASS" ? "text-emerald-600" : "text-rose-600"}`}>
                                    {data.final_result}
                                </p>
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-200">
                            <div className="min-w-0">
                                <p className="text-xs text-slate-500 flex items-center gap-1.5 mb-1"><Scale className="w-3.5 h-3.5"/> Instrument</p>
                                <p className="text-sm font-semibold text-slate-900 break-words">{data.instrument}</p>
                                <p className="text-xs font-mono text-slate-500 mt-0.5 break-all">S/N: {data.serial_number}</p>
                            </div>
                            <div>
                                <p className="text-xs text-slate-500 flex items-center gap-1.5 mb-1"><Calendar className="w-3.5 h-3.5"/> Test Date</p>
                                <p className="text-sm font-semibold text-slate-900">{format(new Date(data.test_date), "MMM d, yyyy")}</p>
                            </div>
                        </div>
                    </div>

                    {/* Meta information list */}
                    <ul className="space-y-3 px-0 sm:px-2">
                        <li className="flex justify-between items-start gap-4 text-sm">
                            <span className="text-slate-500 shrink-0">Standard / Rule Version:</span>
                            <span className="font-semibold text-slate-800 text-right break-words min-w-0">{data.standard_version}</span>
                        </li>
                        <li className="flex justify-between items-start gap-4 text-sm">
                            <span className="text-slate-500 shrink-0">Report Status:</span>
                            <span className="font-semibold text-slate-800 text-right break-words min-w-0">{data.report_status}</span>
                        </li>
                        <li className="flex justify-between items-start gap-4 text-sm">
                            <span className="text-slate-500 shrink-0">Generated At:</span>
                            <span className="font-semibold text-slate-800 text-right break-words min-w-0">{format(new Date(data.generated_at), "yyyy-MM-dd HH:mm")}</span>
                        </li>
                        <li className="flex justify-between items-start gap-4 text-sm">
                            <span className="text-slate-500 shrink-0">Verification Scans:</span>
                            <span className="font-semibold text-slate-800 bg-slate-100 px-2 rounded-full">{data.scans_count}</span>
                        </li>
                    </ul>

                    {/* Disclaimer */}
                    <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
                        <p className="text-xs text-amber-800 leading-relaxed font-medium">
                            <strong className="block mb-1">PROTOTYPE NOTICE:</strong> 
                            This is a prototype test report generated according to configured OIML test-report structure. 
                            It is strictly for demonstration and is NOT an officially approved legal certificate.
                        </p>
                    </div>

                    {/* Download */}
                    <div className="pt-2">
                        <a href={`${API_URL}/reports/${data.report_id}/download`}
                           target="_blank" rel="noreferrer"
                           className="flex w-full items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-bold py-3.5 px-4 rounded-xl shadow-lg transition-all text-sm sm:text-base text-center">
                            <Download className="w-5 h-5" /> Download Full PDF Report
                        </a>
                    </div>
                </div>
            </div>
            
            <p className="mt-6 sm:mt-8 text-xs text-slate-400 font-medium text-center">Powered by MetraSure Compliance Engine</p>
        </div>
    );
}
