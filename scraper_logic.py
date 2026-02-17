# scraper_logic.py
import json
import requests
import re
from google.genai import types
from google_play_scraper import app as scrapper_app
from google_play_scraper import search as scrapper_search

COUNTRY_CODES_MAP = {
    "afghanistan": "AF", "aland islands": "AX", "albania": "AL", "algeria": "DZ", "american samoa": "AS",
    "andorra": "AD", "angola": "AO", "anguilla": "AI", "antarctica": "AQ", "antigua and barbuda": "AG",
    "argentina": "AR", "armenia": "AM", "aruba": "AW", "australia": "AU", "austria": "AT",
    "azerbaijan": "AZ", "bahamas": "BS", "bahrain": "BH", "bangladesh": "BD", "barbados": "BB",
    "belarus": "BY", "belgium": "BE", "belize": "BZ", "benin": "BJ", "bermuda": "BM",
    "bhutan": "BT", "bolivia": "BO", "bonaire, sint eustatius and saba": "BQ", "bosnia and herzegovina": "BA", "botswana": "BW",
    "bouvet island": "BV", "brazil": "BR", "british indian ocean territory": "IO", "brunei darussalam": "BN", "bulgaria": "BG",
    "burkina faso": "BF", "burundi": "BI", "cabo verde": "CV", "cambodia": "KH", "cameroon": "CM",
    "canada": "CA", "cayman islands": "KY", "central african republic": "CF", "chad": "TD", "chile": "CL",
    "china": "CN", "christmas island": "CX", "cocos (keeling) islands": "CC", "colombia": "CO", "comoros": "KM",
    "congo": "CG", "congo, democratic republic of the": "CD", "cook islands": "CK", "costa rica": "CR", "cote d'ivoire": "CI",
    "croatia": "HR", "cuba": "CU", "curacao": "CW", "cyprus": "CY", "czechia": "CZ", "denmark": "DK",
    "djibouti": "DJ", "dominica": "DM", "dominican republic": "DO", "ecuador": "EC", "egypt": "EG",
    "el salvador": "SV", "equatorial guinea": "GQ", "eritrea": "ER", "estonia": "EE", "eswatini": "SZ",
    "ethiopia": "ET", "falkland islands (malvinas)": "FK", "faroe islands": "FO", "fiji": "FJ", "finland": "FI",
    "france": "FR", "french guiana": "GF", "french polynesia": "PF", "french southern territories": "TF", "gabon": "GA",
    "gambia": "GM", "georgia": "GE", "germany": "DE", "ghana": "GH", "gibraltar": "GI",
    "greece": "GR", "greenland": "GL", "grenada": "GD", "guadeloupe": "GP", "guam": "GU",
    "guatemala": "GT", "guernsey": "GG", "guinea": "GN", "guinea-bissau": "GW", "guyana": "GY",
    "haiti": "HT", "heard island and mcdonald islands": "HM", "holy see": "VA", "honduras": "HN", "hong kong": "HK",
    "hungary": "HU", "iceland": "IS", "india": "IN", "indonesia": "ID", "iran": "IR",
    "iraq": "IQ", "ireland": "IE", "isle of man": "IM", "israel": "IL", "italy": "IT",
    "jamaica": "JM", "japan": "JP", "jersey": "JE", "jordan": "JO", "kazakhstan": "KZ",
    "kenya": "KE", "kiribati": "KI", "korea, democratic people's republic of": "KP", "korea, republic of": "KR", "south korea": "KR",
    "kuwait": "KW", "kyrgyzstan": "KG", "lao people's democratic republic": "LA", "latvia": "LV", "lebanon": "LB",
    "lesotho": "LS", "liberia": "LR", "libya": "LY", "liechtenstein": "LI", "lithuania": "LT",
    "luxembourg": "LU", "macao": "MO", "madagascar": "MG", "malawi": "MW", "malaysia": "MY",
    "maldives": "MV", "mali": "ML", "malta": "MT", "marshall islands": "MH", "martinique": "MQ",
    "mauritania": "MR", "mauritius": "MU", "mayotte": "YT", "mexico": "MX", "micronesia": "FM",
    "moldova": "MD", "monaco": "MC", "mongolia": "MN", "montenegro": "ME", "montserrat": "MS",
    "morocco": "MA", "mozambique": "MZ", "myanmar": "MM", "namibia": "NA", "nauru": "NR",
    "nepal": "NP", "netherlands": "NL", "new caledonia": "NC", "new zealand": "NZ", "nicaragua": "NI",
    "niger": "NE", "nigeria": "NG", "niue": "NU", "norfolk island": "NF", "northern mariana islands": "MP",
    "norway": "NO", "oman": "OM", "pakistan": "PK", "palau": "PW", "palestine, state of": "PS",
    "panama": "PA", "papua new guinea": "PG", "paraguay": "PY", "peru": "PE", "philippines": "PH",
    "pitcairn": "PN", "poland": "PL", "portugal": "PT", "puerto rico": "PR", "qatar": "QA",
    "reunion": "RE", "romania": "RO", "russian federation": "RU", "russia": "RU", "rwanda": "RW",
    "saint barthelemy": "BL", "saint helena, ascension and tristan da cunha": "SH", "saint kitts and nevis": "KN", "saint lucia": "LC",
    "saint martin (french part)": "MF", "saint pierre and miquelon": "PM", "saint vincent and the grenadines": "VC", "samoa": "WS",
    "san marino": "SM", "sao tome and principe": "ST", "saudi arabia": "SA", "senegal": "SN", "serbia": "RS",
    "seychelles": "SC", "sierra leone": "SL", "singapore": "SG", "sint maarten (dutch part)": "SX", "slovakia": "SK",
    "slovenia": "SI", "solomon islands": "SB", "somalia": "SO", "south africa": "ZA", "south georgia and the south sandwich islands": "GS",
    "south sudan": "SS", "spain": "ES", "sri lanka": "LK", "sudan": "SD", "suriname": "SR",
    "svalbard and jan mayen": "SJ", "swaziland": "SZ", "sweden": "SE", "switzerland": "CH", "syrian arab republic": "SY",
    "taiwan": "TW", "tajikistan": "TJ", "tanzania, united republic of": "TZ", "thailand": "TH", "timor-leste": "TL",
    "togo": "TG", "tokelau": "TK", "tonga": "TO", "trinidad and tobago": "TT", "tunisia": "TN",
    "turkey": "TR", "turkmenistan": "TM", "turks and caicos islands": "TC", "tuvalu": "TV", "uganda": "UG",
    "ukraine": "UA", "united arab emirates": "AE", "united kingdom": "GB", "uk": "GB", "united states": "US", "usa": "US",
    "united states minor outlying islands": "UM", "uruguay": "UY", "uzbekistan": "UZ", "vanuatu": "VU",
    "venezuela": "VE", "vietnam": "VN", "virgin islands, british": "VG", "virgin islands, u.s.": "VI", "wallis and futuna": "WF",
    "western sahara": "EH", "yemen": "YE", "zambia": "ZM", "zimbabwe": "ZW"
}

def translate_country_to_code(region_name):
    """
    Translates a country name to a 2-letter ISO code.
    If it's already a 2-letter code, returns it.
    """
    if not region_name:
        return "US"
    
    clean_name = region_name.strip().lower()
    
    # Already a code?
    if len(clean_name) == 2 and clean_name.isalpha():
        return clean_name.upper()
    
    # Try mapping
    return COUNTRY_CODES_MAP.get(clean_name, clean_name.upper()) # Return upper version of input if unknown

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

def verify_package_exists(package_name, region="US", use_fallbacks=False):
    """
    Sends an HTTP GET request to the Google Play Store.
    Returns the successful region code if the app exists, None otherwise.
    """
    regions_to_try = [region]
    if use_fallbacks:
        # Expanding fallbacks to major global markets
        fallbacks = ["US", "IN", "CN", "BR", "AR", "DE", "ZA"]
        for f in fallbacks:
            if f not in regions_to_try:
                regions_to_try.append(f)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for r in regions_to_try:
        url = f"https://play.google.com/store/apps/details?id={package_name}&gl={r}"
        try:
            print(f"Checking: {package_name} (region: {r})...", end=" ")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("✅ Exists!")
                return r
            elif response.status_code == 404:
                print("❌ Not Found (404)")
            else:
                print(f"⚠️ Unexpected Status: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
            
    return None

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

def get_package_by_name(query, region="US"):
    """
    Searches Play Store for a query and extracts package IDs from the results.
    """
    url = f"https://play.google.com/store/search?q={query}&c=apps&gl={region}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)         
        # Improved regex to catch both absolute and relative links
        pattern = r"(?:/store/apps/details\?id=|https://play\.google\.com/store/apps/details\?id=)([a-zA-Z0-9._]+)"
        
        # Extract and deduplicate while preserving order of appearance
        matches = re.findall(pattern, response.text)
        package_names = []
        seen = set()
        for pkg in matches:
            if pkg not in seen:
                package_names.append(pkg)
                seen.add(pkg)
                print(f"Found Package Name: {pkg}")
        
        return package_names
            
    except Exception as e:
        print(f"Error searching for {query}: {e}")
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

def get_app_details(package_id, region="US"):
    """
    Fetches app details from Google Play Store using google_play_scraper.
    """
    from google_play_scraper import app as play_app
    try:
        details = play_app(
            package_id,
            lang='en', # defaults to 'en'
            country=region.lower() if region else 'us'
        )
        return details
    except Exception as e:
        print(f"Error fetching app details for {package_id}: {e}")
        return None

def process_results(raw_apps, region, resolve_with_ai, client, model_name, category=""):
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
        working_region = verify_package_exists(pkg, region=region)
        if not working_region:
            print(f"❌ Initial package {pkg} failed. Searching...")            
            search_query = f"{name} ({category})" if category else name
            pkgs = get_package_by_name(search_query, region=region)
            if len(pkgs)>0:
                print(f"✅ Found via web search: {pkgs[0]}")
                pkg = pkgs[0]
                working_region = verify_package_exists(pkg, region=region) # Check again with working search result
                status = "Verified" if working_region else "Not Found"
            elif resolve_with_ai:
                ai_pkg = find_id_via_gemini(client, [name], model_name)
                working_region = verify_package_exists(ai_pkg, region=region) if ai_pkg else None
                if working_region:
                    print(f"✅ Found via AI: {ai_pkg}")
                    pkg = ai_pkg
                    status = "Verified"
                else:
                    print(f"❌ Not Found via AI: {name}")
                    status = "Not Found"
            else:
                status = "Not Found"
        else:
            status = "Verified"
        
        # Use fallback region if primary failed
        effective_region = working_region if working_region else region
        
        app['package'] = pkg
        app['status'] = status
        app['region'] = effective_region # Store the working region
        
        if status == "Verified":
            app['play_store_url'] = f"https://play.google.com/store/apps/details?id={pkg}&gl={effective_region}"
        else:
            search_query = f"{name} ({category})" if category else name
            app['play_store_url'] = f"https://play.google.com/store/search?q={search_query}&c=apps&gl={region}"
        processed_list.append(app)
        
    return processed_list