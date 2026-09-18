import os
from google import genai
from google.genai.errors import APIError
from openai import OpenAI

# 1. Configure your Free API Keys (Or set these in your environment variables)
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_FREE_GOOGLE_AI_STUDIO_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_FREE_OPENROUTER_KEY")

def generate_code_with_failover(prompt: str) -> str:
    print("🤖 Attempting primary engine: Google AI Studio (Gemini)...")
    
    # --- PRIMARY ENGINE: GEMINI ---
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',  # Ultra-fast open tier model
            contents=prompt,
        )
        print("✅ Primary engine succeeded!")
        return response.text

    # --- FALLBACK ENGINE: OPENROUTER (DEEPSEEK) ---
    except (APIError, Exception) as e:
        print(f"⚠️ Primary engine failed or rate-limited: {e}")
        print("🔄 Switching to secondary engine: OpenRouter...")
        
        try:
            # OpenRouter uses the standard OpenAI structure
            client = OpenAI(
                base_url="https://openrouter.ai",
                api_key=OPENROUTER_API_KEY,
            )
            
            response = client.chat.completions.create(
                model="deepseek/deepseek-r1:free", # Targets the free tier model
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            print("✅ Secondary engine saved the day!")
            return response.choices[0].message.content
            
        except Exception as fallback_error:
            return f"❌ All engines failed. Fallback error: {fallback_error}"

# --- Test the Script ---
if __name__ == "__main__":
    freelance_prompt = "Write a python function to scrape metadata from a URL safely."
    result = generate_code_with_failover(freelance_prompt)
    print("\n--- AI Response ---")
    print(result)
