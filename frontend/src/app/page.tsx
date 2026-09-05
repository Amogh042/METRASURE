"use client";
export default function Home() {
    if (typeof window !== "undefined") {
        window.location.href = "/login";
    }
    return <div className="p-8 text-center text-gray-500">Redirecting to login...</div>;
}
