# gemini_client.py
import os
from google import genai

def ask_gemini(prompt: str, model: str = "gemini-2.5-flash", thinking_budget: int = None) -> str:
    # Create client with API key
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    gen_kwargs = {}
    if thinking_budget is not None:
        from google.genai import types
        gen_kwargs["config"] = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
        )
    
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        **gen_kwargs
    )
    return response.text

if __name__ == "__main__":
    prompt = "You are a senior data analyst. Summarize anomalies in the following dataset: ... (replace with actual data summary / anomalies)."
    result = ask_gemini(prompt)
    print("Gemini says:\n", result)
