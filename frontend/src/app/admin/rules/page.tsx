"use client";

import { useEffect, useState } from "react";
import { getRules, createRule, updateRule, getRuleAudit, API_URL, getToken } from "@/lib/api";
import { Settings, Plus, Edit2, History, Check, X, AlertTriangle, ShieldCheck } from "lucide-react";
import { format } from "date-fns";
import { useRouter } from "next/navigation";

export default function AdminRulesPage() {
    const router = useRouter();
    const [rules, setRules] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [editingRule, setEditingRule] = useState<any>(null);
    const [auditLog, setAuditLog] = useState<any[]>([]);
    const [showAudit, setShowAudit] = useState(false);
    
    // Form state
    const [formData, setFormData] = useState<any>({});
    const [formReason, setFormReason] = useState("");

    const fetchAllRules = async () => {
        try {
            setLoading(true);
            const data = await getRules();
            setRules(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!getToken()) {
            router.push("/login");
            return;
        }
        fetchAllRules();
    }, []);

    const handleEditClick = (rule: any) => {
        setEditingRule(rule);
        setFormData({ ...rule });
        setFormReason("");
    };

    const handleCreateClick = () => {
        setEditingRule({ id: "NEW" });
        setFormData({
            rule_id: "",
            standard: "OIML R-76",
            standard_version: "2006",
            test_type: "Accuracy",
            accuracy_class: "III",
            condition: "Always",
            formula_reference: "",
            permissible_error: 1.0,
            unit: "e",
            notes: "",
            enabled: true
        });
        setFormReason("");
    };

    const handleViewAudit = async (rule: any) => {
        try {
            const logs = await getRuleAudit(rule.id);
            setAuditLog(logs);
            setShowAudit(true);
        } catch (err: any) {
            alert("Failed to load audit logs: " + err.message);
        }
    };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formReason) {
            alert("An audit reason is required for any rule modification.");
            return;
        }

        try {
            const payload = { ...formData, reason: formReason };
            
            if (editingRule.id === "NEW") {
                await createRule(payload);
            } else {
                await updateRule(editingRule.id, payload);
            }
            
            setEditingRule(null);
            fetchAllRules();
        } catch (err: any) {
            alert("Failed to save rule: " + err.message);
        }
    };

    const handleToggleEnable = async (rule: any) => {
        const reason = prompt(`Reason for ${rule.enabled ? 'deactivating' : 'activating'} rule ${rule.rule_id}?`);
        if (!reason) return;
        
        try {
            await updateRule(rule.id, { enabled: !rule.enabled, reason });
            fetchAllRules();
        } catch (err: any) {
            alert("Failed to toggle rule: " + err.message);
        }
    };

    if (loading && rules.length === 0) return <div className="p-8 text-center text-slate-500 font-medium">Loading compliance rules...</div>;
    if (error) return <div className="p-4 bg-red-50 text-red-700 m-6 rounded-lg font-medium">{error}</div>;

    return (
        <div className="max-w-7xl mx-auto space-y-6 relative">
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                        <ShieldCheck className="w-6 h-6 text-indigo-600" />
                        OIML Rule Engine Configuration
                    </h1>
                    <p className="text-sm text-slate-500 mt-1">Admin-only area. Modifications are strictly audited and versioned.</p>
                </div>
                <button 
                    onClick={handleCreateClick}
                    className="bg-indigo-600 text-white font-semibold py-2 px-4 rounded-lg hover:bg-indigo-700 shadow-sm text-sm flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" /> Create Rule
                </button>
            </div>

            {/* Rules Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                        <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                            <tr>
                                <th className="px-5 py-3 text-left">Rule ID</th>
                                <th className="px-5 py-3 text-left">Standard</th>
                                <th className="px-5 py-3 text-left">Test & Class</th>
                                <th className="px-5 py-3 text-left">Formula</th>
                                <th className="px-5 py-3 text-left">MPE</th>
                                <th className="px-5 py-3 text-left">Status</th>
                                <th className="px-5 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 bg-white">
                            {rules.map(rule => (
                                <tr key={rule.id} className="hover:bg-slate-50/70 transition-colors">
                                    <td className="px-5 py-3">
                                        <span className="font-mono font-bold text-slate-800">{rule.rule_id}</span>
                                    </td>
                                    <td className="px-5 py-3 text-slate-600">
                                        {rule.standard} <span className="text-xs text-slate-400">({rule.standard_version})</span>
                                    </td>
                                    <td className="px-5 py-3 text-slate-700">
                                        {rule.test_type} <span className="text-xs bg-slate-100 px-1 rounded ml-1">Cl. {rule.accuracy_class}</span>
                                    </td>
                                    <td className="px-5 py-3">
                                        <code className="text-xs bg-slate-100 text-pink-600 px-1.5 py-0.5 rounded">{rule.formula_reference}</code>
                                    </td>
                                    <td className="px-5 py-3 font-semibold text-slate-700">
                                        {rule.permissible_error} {rule.unit}
                                    </td>
                                    <td className="px-5 py-3">
                                        {rule.enabled ? (
                                            <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                                                ACTIVE
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                                                INACTIVE
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-5 py-3 text-right space-x-3">
                                        <button onClick={() => handleViewAudit(rule)} className="text-slate-400 hover:text-blue-600 transition-colors" title="Audit Log">
                                            <History className="w-4 h-4 inline" />
                                        </button>
                                        <button onClick={() => handleEditClick(rule)} className="text-slate-400 hover:text-indigo-600 transition-colors" title="Edit Rule">
                                            <Edit2 className="w-4 h-4 inline" />
                                        </button>
                                        <button 
                                            onClick={() => handleToggleEnable(rule)} 
                                            className={`${rule.enabled ? 'text-rose-400 hover:text-rose-600' : 'text-emerald-400 hover:text-emerald-600'} transition-colors`}
                                            title={rule.enabled ? "Deactivate" : "Activate"}
                                        >
                                            {rule.enabled ? <X className="w-4 h-4 inline" /> : <Check className="w-4 h-4 inline" />}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Edit / Create Modal */}
            {editingRule && (
                <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-slate-200">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50 sticky top-0">
                            <h2 className="text-xl font-bold text-slate-800">
                                {editingRule.id === "NEW" ? "Create New Engine Rule" : `Edit Rule: ${editingRule.rule_id}`}
                            </h2>
                            <button onClick={() => setEditingRule(null)} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5"/></button>
                        </div>
                        <form onSubmit={handleSave} className="p-6 space-y-4">
                            
                            <div className="bg-amber-50 border border-amber-200 text-amber-800 p-3 rounded-lg text-sm flex gap-2 items-start mb-4">
                                <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                                <div>
                                    <p className="font-bold">Strict Audit Notice</p>
                                    <p className="mt-0.5">Rules used in historical compliance testing cannot have their core values modified. Create a new rule version and deactivate this one instead.</p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Rule ID</label>
                                    <input type="text" value={formData.rule_id} onChange={e => setFormData({...formData, rule_id: e.target.value})} className="w-full border border-slate-300 rounded p-2 text-sm" required />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Test Type</label>
                                    <select value={formData.test_type} onChange={e => setFormData({...formData, test_type: e.target.value})} className="w-full border border-slate-300 rounded p-2 text-sm">
                                        <option value="Accuracy">Accuracy</option>
                                        <option value="Repeatability">Repeatability</option>
                                        <option value="Eccentricity">Eccentricity</option>
                                        <option value="Zero">Zero</option>
                                        <option value="Tare">Tare</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Accuracy Class</label>
                                    <select value={formData.accuracy_class} onChange={e => setFormData({...formData, accuracy_class: e.target.value})} className="w-full border border-slate-300 rounded p-2 text-sm">
                                        <option value="I">I</option>
                                        <option value="II">II</option>
                                        <option value="III">III</option>
                                        <option value="IIII">IIII</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Standard & Version</label>
                                    <div className="flex gap-2">
                                        <input type="text" value={formData.standard} onChange={e => setFormData({...formData, standard: e.target.value})} className="w-2/3 border border-slate-300 rounded p-2 text-sm" required />
                                        <input type="text" value={formData.standard_version} onChange={e => setFormData({...formData, standard_version: e.target.value})} className="w-1/3 border border-slate-300 rounded p-2 text-sm" required />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Condition</label>
                                    <input type="text" value={formData.condition} onChange={e => setFormData({...formData, condition: e.target.value})} placeholder="e.g. 0 <= m <= 500e" className="w-full border border-slate-300 rounded p-2 text-sm" required />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Formula Reference</label>
                                    <input type="text" value={formData.formula_reference} onChange={e => setFormData({...formData, formula_reference: e.target.value})} placeholder="e.g. 1e" className="w-full border border-slate-300 rounded p-2 text-sm" required />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Permissible Error</label>
                                    <div className="flex gap-2">
                                        <input type="number" step="0.01" value={formData.permissible_error} onChange={e => setFormData({...formData, permissible_error: parseFloat(e.target.value)})} className="w-2/3 border border-slate-300 rounded p-2 text-sm" required />
                                        <input type="text" value={formData.unit} onChange={e => setFormData({...formData, unit: e.target.value})} placeholder="Unit" className="w-1/3 border border-slate-300 rounded p-2 text-sm" required />
                                    </div>
                                </div>
                                
                                <div className="col-span-2 border-t border-slate-200 my-2 pt-4">
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Audit Reason (Required)</label>
                                    <input type="text" value={formReason} onChange={e => setFormReason(e.target.value)} placeholder="Explain why this rule is being created/modified..." className="w-full border border-rose-300 rounded p-2 text-sm focus:ring-rose-500 focus:border-rose-500 bg-rose-50" required />
                                </div>
                            </div>
                            
                            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-100">
                                <button type="button" onClick={() => setEditingRule(null)} className="px-4 py-2 text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors">Cancel</button>
                                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-colors shadow-sm">Save Rule</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Audit Log Modal */}
            {showAudit && (
                <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col border border-slate-200">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2"><History className="w-5 h-5"/> Rule Audit Log</h2>
                            <button onClick={() => setShowAudit(false)} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5"/></button>
                        </div>
                        <div className="p-6 overflow-y-auto flex-1 bg-slate-50/50">
                            {auditLog.length === 0 ? (
                                <p className="text-center text-slate-500 py-8">No audit logs found for this rule.</p>
                            ) : (
                                <div className="space-y-6">
                                    {auditLog.map(log => (
                                        <div key={log.id} className="relative pl-6 border-l-2 border-indigo-200">
                                            <div className="absolute w-3 h-3 bg-indigo-500 rounded-full -left-[7px] top-1.5 ring-4 ring-white"></div>
                                            <div className="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div>
                                                        <span className="font-bold text-slate-800">{log.action}</span>
                                                        <span className="text-sm text-slate-500 ml-2">by Admin (User ID: {log.user_id})</span>
                                                    </div>
                                                    <span className="text-xs font-mono text-slate-400">{format(new Date(log.timestamp), "yyyy-MM-dd HH:mm:ss")}</span>
                                                </div>
                                                <p className="text-sm text-slate-700 bg-slate-50 p-2 rounded border border-slate-100 mb-3"><span className="font-bold">Reason:</span> {log.reason}</p>
                                                
                                                {log.action === "UPDATE" && (
                                                    <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                                                        <div className="bg-rose-50 p-3 rounded border border-rose-100 overflow-x-auto">
                                                            <p className="font-bold text-rose-800 mb-1 border-b border-rose-200 pb-1">Previous Value</p>
                                                            <pre className="text-rose-700">{JSON.stringify(JSON.parse(log.previous_value || "{}"), null, 2)}</pre>
                                                        </div>
                                                        <div className="bg-emerald-50 p-3 rounded border border-emerald-100 overflow-x-auto">
                                                            <p className="font-bold text-emerald-800 mb-1 border-b border-emerald-200 pb-1">New Value</p>
                                                            <pre className="text-emerald-700">{JSON.stringify(JSON.parse(log.new_value || "{}"), null, 2)}</pre>
                                                        </div>
                                                    </div>
                                                )}
                                                
                                                {log.action === "CREATE" && (
                                                    <div className="text-xs font-mono bg-emerald-50 p-3 rounded border border-emerald-100 overflow-x-auto">
                                                        <pre className="text-emerald-700">{JSON.stringify(JSON.parse(log.new_value || "{}"), null, 2)}</pre>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
