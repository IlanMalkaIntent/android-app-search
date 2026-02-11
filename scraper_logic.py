# scraper_logic.py
import json
import requests
import re
from google.genai import types
from google_play_scraper import app as scrapper_app
from google_play_scraper import search as scrapper_search

def get_market_research(topic, region, client, model_name):
    """
    Uses Gemini to generate the initial list of apps.
    """
    prompt = f"""
    Act as a Senior Mobile Market Researcher.
    
    Goal: Identify the top downloaded and most relevant Android applications used '{topic}' in '{region}'.
    
    Filtering Criteria:
    - Include: Apps specifically designed for {topic} (User Intent).
    - Exclude: Generic super-apps, web browsers, or apps that do not primarily serve this function.
    - Source: Focus on current Google Play Store rankings and popularity in {region}.
    - When resolving the app name, look for the latest name in the google play sßtore, since sometimes it is being changed by the developers. 
    - Do not guess the package name, use the app name to search the exact package name on the google play store web site.
    - Give priority for Apps that are popular in {region}
    
    
    Output Requirements:
    1. Return ONLY a JSON array. Do not write sentences.
    2. Do not use markdown formatting.
    3. For every single app found, the 'weight' field MUST be set to exactly 1.0. Do not calculate this value; hardcode it.
    
    
    Required JSON Structure:
    [
      {{
        "package": "Exact package name as found on Google Play Store",
        "name": "Exact App Name",
        "weight": 1.0
      }}
    ]
    """
    
    try:
        response = client.models.generate_content(
            model=model_name, 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False
                ) if "thinking" in model_name else None, # Only add thinking_config if supported
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        text = response.text
        # Clean up markdown fences if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        return json.loads(text.strip())
    except Exception as e:
        print(f"Gemini Error: {e}")
        return []

def verify_package_exists(package_name):
    """
    Sends an HTTP GET request to the Google Play Store.
    Returns True if the app exists (Status 200), False otherwise.
    """
    url = f"https://play.google.com/store/apps/details?id={package_name}"
    
    # ⚠️ CRITICAL: You must use a 'User-Agent' header.
    # Without it, Google blocks the request as a bot (Error 403/429).
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        print(f"Checking: {package_name}...", end=" ")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Exists!")
            return True
        elif response.status_code == 404:
            print("❌ Not Found (404)")
            return False
        else:
            print(f"⚠️ Unexpected Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def search_play_store_for_id(app_name, region="US"):
    """
    Uses google-play-scraper to find the ID (Free, fast).
    """
    try:
        results = scrapper_search(app_name, country=region, n_hits=1)
        if results:
            return results[0]['appId']
    except Exception as e:
        print(f"Scraper Error: {e}")
    return None

def get_package_by_name(package_name):
    """
    Sends an HTTP GET request to the Google Play Store.
    Returns True if the app exists (Status 200), False otherwise.
    """
    url = f"https://play.google.com/store/search?q={package_name}&c=apps"
    
    # ⚠️ CRITICAL: You must use a 'User-Agent' header.
    # Without it, Google blocks the request as a bot (Error 403/429).
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:

        response = requests.get(url, headers=headers, timeout=10)         
        pattern = r"https://play\.google\.com/store/apps/details\?id=([a-zA-Z0-9._]+)"
        # 3. Extract all matches
        package_names = re.findall(pattern, response.text)
        
        # 4. Print results
        for pkg in package_names:
            print(f"Found Package Name: {pkg}")
        return package_names
            
    except Exception as e:
        print(f"Error: {e}")
        return []


def find_id_via_gemini(client, app_names, model_name):
    print(f"   🤖 Asking Gemini to find ID for: {app_names[0]}...")
    
    prompt = f"""
    Find the exact Google Play Store Package ID for the Android app "{app_names[0]}".
    1. Use Google Search to find the official Play Store URL.
    2. Extract the text after 'id='.
    3. Return ONLY the package ID string (e.g., com.example.app). Do not write sentences.

    Required JSON Structure: {{"{app_names[0]}" : "com.example.app"}}
    """
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                http_options=types.HttpOptions(timeout=90_000),
                # Enable Google Search Tool
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        text = response.text
        # Clean up markdown fences
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        res = json.loads(text.strip())
        # The user's prompt suggests getting back a dict
        if isinstance(res, dict):
            # Try to get the first value
            return list(res.values())[0]
        return text.strip()
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def list_supported_models(client):
    """
    Returns a list of available model IDs for the given client.
    """
    try:
        print("Fetching models from Gemini API...")
        models = list(client.models.list())
        print(f"Found {len(models)} models total.")
        
        # Log some for debugging
        for m in models[:5]:
            print(f"Model ID: {m.name}")
            
        # Try to find models that support generation
        # Some SDK versions might use different attribute names
        gen_models = [m.name for m in models if hasattr(m, 'supported_methods') and any("generateContent" in meth for meth in m.supported_methods)]
        
        if not gen_models:
            print("Warning: No generation models found via filter. Returning all models.")
            return [m.name for m in models]
            
        return gen_models
    except Exception as e:
        print(f"Error listing models: {e}")
        return []

def get_app_details(package_id):
    """
    Fetches app details from Google Play Store using google_play_scraper.
    """
    from google_play_scraper import app as play_app
    try:
        details = play_app(
            package_id,
            lang='en', # defaults to 'en'
            country='us' # defaults to 'us'
        )
        return details
    except Exception as e:
        print(f"Error fetching app details for {package_id}: {e}")
        return None

def process_results(raw_apps, region, resolve_with_ai, client, model_name):
    """
    Main orchestration logic.
    """
    processed_list = []
    
    for app in raw_apps:
        pkg = app.get('package')
        name = app.get('name')
        status = "Verified"
        
        # 1. Verify the AI's initial guess
        print(f"🔍 Checking: {name} - {pkg}...")
        if not verify_package_exists(pkg):
            print(f"❌ Initial package {pkg} failed. Searching...")            
            pkgs = get_package_by_name(app['name'])
            if len(pkgs)>0:
                print(f"✅ Found via web search: {pkgs[0]}")
                pkg = pkgs[0]
            elif resolve_with_ai:
                ai_pkg = find_id_via_gemini(client, [name], model_name)
                if ai_pkg and verify_package_exists(ai_pkg):
                    print(f"✅ Found via AI: {ai_pkg}")
                    pkg = ai_pkg
                else:
                    print(f"❌ Not Found via AI: {name}")
                    status = "Not Found"
            else:
                status = "Not Found"
        
        app['package'] = pkg
        app['status'] = status
        if status == "Verified":
            app['play_store_url'] = f"https://play.google.com/store/apps/details?id={pkg}"
        else:
            app['play_store_url'] = f"https://play.google.com/store/search?q={name}&c=apps"
        processed_list.append(app)
        
    return processed_list