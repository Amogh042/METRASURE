"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function LoginPage() {
    const router = useRouter();
    const [username, setUsername] = useState("tech");
    const [password, setPassword] = useState("tech123");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            await login(username, password);
            router.push("/dashboard");
        } catch (err: any) {
            setError(err.message || "Login failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[75vh] flex items-center justify-center">
            <div className="bg-white p-8 rounded-lg shadow-lg border border-gray-200 w-full max-w-md">
                <div className="text-center mb-6">
                    <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mx-auto mb-3">
                        <span className="text-white font-bold text-xl">M</span>
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900">MetraSure</h1>
                    <p className="text-sm text-gray-500 mt-1">NAWI Test Report System</p>
                </div>
                {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded mb-4 text-sm">{error}</div>}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                        <input type="text" value={username} onChange={e => setUsername(e.target.value)} required
                            className="block w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                        <input type="password" value={password} onChange={e => setPassword(e.target.value)} required
                            className="block w-full rounded-md border border-gray-300 shadow-sm px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500" />
                    </div>
                    <button type="submit" disabled={loading}
                        className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-colors">
                        {loading ? "Signing in..." : "Sign In"}
                    </button>
                </form>
                <p className="mt-4 text-xs text-center text-gray-400">Demo accounts: admin / officer / tech (password: [name]123)</p>
            </div>
        </div>
    );
}
