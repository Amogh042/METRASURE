"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createInstrument, getToken } from "@/lib/api";

export default function NewInstrument() {
    const router = useRouter();
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        instrument_id: "",
        manufacturer: "",
        model: "",
        serial_number: "",
        instrument_type: "NAWI",
        accuracy_class: "III",
        max_capacity: "",
        min_capacity: "",
        verification_interval: "",
        unit: "kg",
        owner: "",
        location: "",
    });

    if (typeof window !== "undefined" && !getToken()) { window.location.href = "/login"; }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const payload = {
                ...formData,
                max_capacity: parseFloat(formData.max_capacity),
                min_capacity: parseFloat(formData.min_capacity),
                verification_interval: parseFloat(formData.verification_interval),
            };
            await createInstrument(payload);
            router.push("/instruments");
        } catch (err: any) {
            setError(err.message || "Failed to register instrument");
        } finally {
            setLoading(false);
        }
    };

    const fieldClass = "block w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500";

    return (
        <div className="max-w-2xl mx-auto">
            <h1 className="text-2xl font-bold mb-5 text-gray-900">Register New Instrument</h1>
            {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded mb-4 text-sm">{error}</div>}
            <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-5">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Instrument ID</label>
                        <input required type="text" name="instrument_id" value={formData.instrument_id} onChange={handleChange} placeholder="e.g. INST-006" className={fieldClass} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Manufacturer</label>
                        <input required type="text" name="manufacturer" value={formData.manufacturer} onChange={handleChange} className={fieldClass} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                        <input required type="text" name="model" value={formData.model} onChange={handleChange} className={fieldClass} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Serial Number</label>
                        <input required type="text" name="serial_number" value={formData.serial_number} onChange={handleChange} className={fieldClass} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Instrument Type</label>
                        <input required type="text" name="instrument_type" value={formData.instrument_type} onChange={handleChange} className={fieldClass} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Accuracy Class</label>
                        <select name="accuracy_class" value={formData.accuracy_class} onChange={handleChange} className={fieldClass}>
                            <option value="I">I (Special)</option>
                            <option value="II">II (High)</option>
                            <option value="III">III (Medium)</option>
                            <option value="IIII">IIII (Ordinary)</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Max Capacity</label>
                        <input required type="number" step="any" name="max_capacity" value={formData.max_capacity} onChange={handleChange} className={fieldClass} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Min Capacity</label>
                        <input required type="number" step="any" name="min_capacity" value={formData.min_capacity} onChange={handleChange} className={fieldClass} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Verification Interval (e)</label>
                        <input required type="number" step="any" name="verification_interval" value={formData.verification_interval} onChange={handleChange} className={fieldClass} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
                        <select name="unit" value={formData.unit} onChange={handleChange} className={fieldClass}>
                            <option value="kg">kg</option>
                            <option value="g">g</option>
                            <option value="mg">mg</option>
                            <option value="t">t</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Owner</label>
                        <input type="text" name="owner" value={formData.owner} onChange={handleChange} className={fieldClass} />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                        <input type="text" name="location" value={formData.location} onChange={handleChange} className={fieldClass} />
                    </div>
                </div>
                <div className="pt-3 flex justify-end space-x-3 border-t border-gray-100">
                    <button type="button" onClick={() => router.back()} className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">Cancel</button>
                    <button type="submit" disabled={loading} className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md shadow-sm hover:bg-blue-700 disabled:opacity-50 transition-colors">
                        {loading ? "Registering..." : "Register Instrument"}
                    </button>
                </div>
            </form>
        </div>
    );
}
