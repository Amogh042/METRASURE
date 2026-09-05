export const API_URL = "http://localhost:8000/api";

// --- Auth ---
let _token: string | null = null;

export function setToken(token: string) {
    _token = token;
    if (typeof window !== "undefined") {
        localStorage.setItem("metrasure_token", token);
    }
}

export function getToken(): string | null {
    if (_token) return _token;
    if (typeof window !== "undefined") {
        _token = localStorage.getItem("metrasure_token");
    }
    return _token;
}

function authHeaders(): Record<string, string> {
    const token = getToken();
    if (!token) return { "Content-Type": "application/json" };
    return { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
}

async function handleResponse(res: Response) {
    if (!res.ok) {
        let detail = `Request failed (${res.status})`;
        try {
            const body = await res.json();
            if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
        } catch {}
        throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
}

// --- Auth API ---
export async function login(username: string, password: string) {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);
    const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form,
    });
    const data = await handleResponse(res);
    setToken(data.access_token);
    return data;
}

// --- Instruments ---
export async function fetchInstruments() {
    const res = await fetch(`${API_URL}/instruments/`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

export async function fetchInstrument(id: number) {
    const res = await fetch(`${API_URL}/instruments/${id}`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

export async function createInstrument(data: any) {
    const res = await fetch(`${API_URL}/instruments/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(data),
    });
    return handleResponse(res);
}

// --- Tests ---
export async function createTest(data: { instrument_id: number; test_type: string; notes?: string }) {
    const res = await fetch(`${API_URL}/tests/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(data),
    });
    return handleResponse(res);
}

export async function fetchTest(testId: number) {
    const res = await fetch(`${API_URL}/tests/${testId}`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

export async function fetchTests() {
    const res = await fetch(`${API_URL}/tests/`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

// --- Measurements ---
export async function addMeasurement(testId: number, measurement: any) {
    const res = await fetch(`${API_URL}/tests/${testId}/measurements`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(measurement),
    });
    return handleResponse(res);
}

export async function fetchMeasurements(testId: number, testModule: string) {
    const res = await fetch(`${API_URL}/tests/${testId}/measurements?test_module=${encodeURIComponent(testModule)}`, { 
        headers: authHeaders(), 
        cache: "no-store" 
    });
    return handleResponse(res);
}

export async function deleteMeasurement(testId: number, measId: number) {
    const res = await fetch(`${API_URL}/tests/${testId}/measurements/${measId}`, {
        method: "DELETE",
        headers: authHeaders(),
    });
    return handleResponse(res);
}

// --- Calculate ---
export async function calculateTest(testId: number, testModule: string) {
    const res = await fetch(`${API_URL}/tests/${testId}/calculate?test_module=${encodeURIComponent(testModule)}`, {
        method: "POST",
        headers: authHeaders(),
    });
    return handleResponse(res);
}

// --- Reports ---
export async function getReports() {
    const res = await fetch(`${API_URL}/reports`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

export async function generateReport(testId: number) {
    const res = await fetch(`${API_URL}/reports/${testId}/generate`, {
        method: "POST",
        headers: authHeaders(),
    });
    return handleResponse(res);
}

// Verification doesn't need auth
export async function verifyReport(token: string) {
    const res = await fetch(`${API_URL}/verify/${token}`, { cache: "no-store" });
    if (!res.ok) {
        throw new Error("Verification failed or token invalid");
    }
    return res.json();
}

// --- History & Search ---
export async function searchHistory(params: Record<string, any> = {}) {
    // Filter out empty params
    const cleanParams = Object.fromEntries(Object.entries(params).filter(([_, v]) => v != null && v !== ""));
    const query = new URLSearchParams(cleanParams).toString();
    const res = await fetch(`${API_URL}/history/search?${query}`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

export async function getInstrumentHistoryStats(id: number) {
    const res = await fetch(`${API_URL}/history/instrument/${id}/stats`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

export async function getHistoricalTestDetails(testId: number) {
    const res = await fetch(`${API_URL}/history/test/${testId}/details`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

export async function getTestAIExplanation(testId: number) {
    const res = await fetch(`${API_URL}/history/test/${testId}/ai-explanation`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

// --- Rule Configuration (Admin) ---
export async function getRules() {
    const res = await fetch(`${API_URL}/rules`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}

export async function createRule(data: any) {
    const res = await fetch(`${API_URL}/rules`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(data)
    });
    return handleResponse(res);
}

export async function updateRule(id: number, data: any) {
    const res = await fetch(`${API_URL}/rules/${id}`, {
        method: "PUT",
        headers: authHeaders(),
        body: JSON.stringify(data)
    });
    return handleResponse(res);
}

export async function getRuleAudit(id: number) {
    const res = await fetch(`${API_URL}/rules/${id}/audit`, { headers: authHeaders(), cache: "no-store" });
    return handleResponse(res);
}
