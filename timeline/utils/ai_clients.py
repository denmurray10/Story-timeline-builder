import json
import time
import os
from django.conf import settings
from openai import OpenAI
import google.generativeai as genai
from ..models import AIUsageLog

def _log_ai_usage(user, service, model, prompt_tokens, completion_tokens):
    """Helper to log token usage and estimated cost."""
    total_tokens = prompt_tokens + completion_tokens
    
    # Very rough cost estimates (USD per 1k tokens)
    costs = {
        'deepseek-chat': 0.0002,
        'deepseek-reasoner': 0.0006,
        'gemini-1.5-flash': 0.0001,
        'gemini-1.5-pro': 0.0012,
    }
    cost_per_1k = costs.get(model, 0.0005)
    cost_est = (total_tokens / 1000) * cost_per_1k

    try:
        AIUsageLog.objects.create(
            user=user,
            service_name=service,
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_estimate=cost_est
        )
    except Exception as e:
        print(f"Error logging AI usage: {e}")

def _call_ai_json(prompt, system_message="You are a professional literary analyst. Always respond with valid JSON. Use British English (UK English) for all spelling and grammar.", max_retries=3, deepseek_model="deepseek-chat", prefer_gemini=False, user=None):
    """Helper to call AI and return parsed JSON with retry logic."""
    if not settings.DEEPSEEK_API_KEY and not settings.GEMINI_API_KEY:
        return None
    
    # Reinforce UK English in system message if not already there
    if "British English" not in system_message and "UK English" not in system_message:
        system_message += " IMPORTANT: Always use British English (UK English) for all spelling and grammar (e.g. 'colour', 'realise', 'characterisation')."

    for attempt in range(max_retries):
        try:
            should_use_gemini = (prefer_gemini and settings.GEMINI_API_KEY) or not settings.DEEPSEEK_API_KEY
            if deepseek_model == 'deepseek-reasoner':
                should_use_gemini = False if settings.DEEPSEEK_API_KEY else True

            if should_use_gemini:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model_name = 'gemini-1.5-pro' if deepseek_model == 'deepseek-reasoner' else 'gemini-1.5-flash'
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(f"{system_message}\n\nTask:\n{prompt}")
                content = response.text
                try:
                    _log_ai_usage(user, 'Gemini', model_name, response.usage_metadata.prompt_token_count, response.usage_metadata.candidates_token_count)
                except: pass
            else:
                client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model=deepseek_model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt},
                    ],
                    stream=False,
                    timeout=60
                )
                content = response.choices[0].message.content
                _log_ai_usage(user, 'DeepSeek', deepseek_model, response.usage.prompt_tokens, response.usage.completion_tokens)

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"AI Call Error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return None

def _call_ai_text(prompt, system_message="You are a creative writing assistant. Use British English (UK English) for all spelling and grammar.", max_retries=3, user=None):
    """Helper to call AI and return raw text. Prioritizes DeepSeek."""
    deepseek_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)

    if not deepseek_key and not gemini_key:
        return "Error: AI API Key not configured."
    
    if "British English" not in system_message and "UK English" not in system_message:
        system_message += " IMPORTANT: Always use British English (UK English) for all spelling and grammar (e.g. 'colour', 'behaviour', 'organised')."

    for attempt in range(max_retries):
        try:
            if deepseek_key:
                client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt},
                    ],
                    stream=False
                )
                ai_response = response.choices[0].message.content
                _log_ai_usage(user, 'DeepSeek', 'deepseek-chat', response.usage.prompt_tokens, response.usage.completion_tokens)
                return ai_response
            else:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{system_message}\n\nTask:\n{prompt}")
                ai_response = response.text
                try:
                    _log_ai_usage(user, 'Gemini', 'gemini-1.5-flash', response.usage_metadata.prompt_token_count, response.usage_metadata.candidates_token_count)
                except: pass
                return ai_response
        except Exception as e:
            print(f"AI Text Call Error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return f"Error: {str(e)}"
