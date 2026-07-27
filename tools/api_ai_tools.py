import os
from config import GEMINI_API_KEY, OPENAI_API_KEY

def ask_gemini_api(prompt: str) -> str:
    """Envía un prompt a la API oficial de Google Gemini usando google-genai."""
    if not GEMINI_API_KEY:
        return "❌ Error: GEMINI_API_KEY no configurada. Usa Selenium o configura la clave."
    
    try:
        from google import genai
        # Usar el SDK oficial de Google GenAI
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # gemini-2.5-flash es rápido y barato para tareas generales
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"❌ Error en Gemini API: {e}"

def ask_openai_api(prompt: str, model: str = "gpt-4o-mini") -> str:
    """Envía un prompt a la API de OpenAI."""
    if not OPENAI_API_KEY:
        return "❌ Error: OPENAI_API_KEY no configurada."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error en OpenAI API: {e}"
