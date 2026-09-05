import os
import json
import httpx

class AIExplainer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

    async def explain(self, test_metadata, details):
        if not self.api_key and not self.gemini_key:
            return None # Gracefully disabled if no keys
            
        # Build prompt
        summary = {
            "test_number": test_metadata.test_number,
            "overall_result": test_metadata.overall_result,
            "modules": {}
        }
        
        for d in details:
            mod = d.get("test_module")
            if mod not in summary["modules"]:
                summary["modules"][mod] = []
            
            calc = d.get("calculations", {})
            meas = d.get("measurement", {})
            
            summary["modules"][mod].append({
                "load": getattr(meas, "test_load", "N/A") if meas else "N/A",
                "calculated_error": calc.get("calculated_error"),
                "permissible_limit": calc.get("permissible_error"),
                "result": d.get("result")
            })

        system_prompt = (
            "You are an AI assistant for a Legal Metrology application. "
            "Your ONLY job is to explain the provided deterministic test results in plain language. "
            "DO NOT invent numbers. DO NOT contradict the provided overall_result. "
            "Keep the explanation under 3 sentences. Be concise and professional."
        )
        
        user_prompt = f"Please explain these test results:\n{json.dumps(summary, indent=2)}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if self.api_key:
                    # OpenAI
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": 0.0
                        }
                    )
                    if response.status_code == 200:
                        return response.json()["choices"][0]["message"]["content"].strip()
                elif self.gemini_key:
                    # Gemini
                    response = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}",
                        json={
                            "systemInstruction": {"parts": [{"text": system_prompt}]},
                            "contents": [{"parts": [{"text": user_prompt}]}],
                            "generationConfig": {"temperature": 0.0}
                        }
                    )
                    if response.status_code == 200:
                        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print("AI Explanation Error:", e)
            return None
            
        return None
