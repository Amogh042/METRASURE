"use client";

import { useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { createTest } from "@/lib/api";

export default function NewTestSession() {
    const { id } = useParams();
    const router = useRouter();
    const searchParams = useSearchParams();
    const testType = searchParams.get("type") || "Accuracy";

    useEffect(() => {
        // Automatically create test session and redirect to execution
        createTest({ instrument_id: Number(id), test_type: testType }).then(test => {
            router.push(`/tests/${test.id}/execute`);
        }).catch(err => {
            console.error(err);
            alert("Failed to start test session");
        });
    }, [id, testType, router]);

    return (
        <div className="flex items-center justify-center min-h-[50vh]">
            <p className="text-gray-500 text-lg">Initializing {testType} Test Session...</p>
        </div>
    );
}
