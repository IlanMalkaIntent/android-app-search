# main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google import genai
import scraper_logic
import shutil
import tempfile
import json
import ConfigExport
from fastapi.responses import FileResponse

app = FastAPI()

@app.post("/api/export-binary")
async def export_binary(data: dict):
    
    try:
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as tmpdirname:
            # The encrypt function in ConfigExport writes directly to files in the output_dir
            ConfigExport.encrypt(data, output_dir=tmpdirname)
            
            # Check if any files were actually created
            generated_files = os.listdir(tmpdirname)
            if not generated_files:
                raise HTTPException(status_code=500, detail="No binary files were generated. Check JSON structure.")
            
            # Create a zip file in the system temp directory
            zip_base = os.path.join(tempfile.gettempdir(), "anagog_binary_export")
            zip_path_full = shutil.make_archive(zip_base, 'zip', tmpdirname)
            
            # Return the file and include a header to trigger download
            return FileResponse(
                zip_path_full, 
                media_type='application/zip', 
                filename="anagog_binary_export.zip"
            )
            
    except Exception as e:
        print(f"Export Binary Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class SearchRequest(BaseModel):
    topic: str
    region: str
    resolve_pkg_with_ai: bool = False
    api_key: str
    model_name: str

class AIResolveRequest(BaseModel):
    app_name: str
    api_key: str
    model_name: str

@app.post("/api/ai-resolve")
def ai_resolve(request: AIResolveRequest):
    """
    Manually triggers AI resolution for a specific app name.
    """
    try:
        client = genai.Client(api_key=request.api_key)
        package_id = scraper_logic.find_id_via_gemini(client, [request.app_name], request.model_name)
        return {"package_id": package_id}
    except Exception as e:
        print(f"Server AI Resolve Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return FileResponse('static/index.html')

@app.post("/api/search")
def search_apps(request: SearchRequest):
    try:
        # Initialize Client dynamically
        client = genai.Client(api_key=request.api_key)
        
        # Translate country name to code
        region_code = scraper_logic.translate_country_to_code(request.region)
        
        print(f" Starting search for topic: {request.topic} in region: {region_code} (input: {request.region}) using model: {request.model_name}")
        
        # 1. Get initial list
        raw_results = scraper_logic.get_market_research(
            request.topic, 
            region_code, 
            client, 
            request.model_name
        )
        
        # 2. Process and verify
        final_results = scraper_logic.process_results(
            raw_results, 
            region_code, 
            request.resolve_pkg_with_ai, 
            client,
            request.model_name,
            category=request.topic
        )
        
        return {"data": final_results, "region": region_code}
    except Exception as e:
        # For debugging purposes
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
def get_models(api_key: str):
    try:
        temp_client = genai.Client(api_key=api_key)
        models = scraper_logic.list_supported_models(temp_client)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/verify")
def verify_package(package_name: str, app_name: str = "", region: str = "US", skip_search: bool = False):
    region_code = scraper_logic.translate_country_to_code(region)
    working_region = scraper_logic.verify_package_exists(package_name, region=region_code)
    
    if working_region:
        return {
            "status": "Verified",
            "package": package_name,
            "region": working_region,
            "play_store_url": f"https://play.google.com/store/apps/details?id={package_name}&gl={working_region}"
        }
    
    # Re-use logic: if not found, try searching by name
    if app_name and not skip_search:
        print(f"❌ Verification for {package_name} (region: {region_code}) failed. Attempting search for {app_name}...")
        results = scraper_logic.get_package_by_name(app_name, region=region_code)
        if results:
            new_package = results[0]
            # Try verification with fallbacks for the new package too
            working_region = scraper_logic.verify_package_exists(new_package, region=region_code)
            if working_region:
                print(f"✅ Found alternative via web search: {new_package} (in region: {working_region})")
                return {
                    "status": "Verified",
                    "package": new_package,
                    "region": working_region,
                    "play_store_url": f"https://play.google.com/store/apps/details?id={new_package}&gl={working_region}"
                }
    
    return {
        "status": "Not Found",
        "package": package_name,
        "region": region_code,
        "play_store_url": f"https://play.google.com/store/search?q={app_name}&c=apps&gl={region_code}" if app_name else "#"
    }

@app.get("/api/find-package")
def find_package(app_name: str, region: str = "US"):
    """
    Attempts to find a package ID for a given app name.
    Returns the first matching package ID or None.
    """
    region_code = scraper_logic.translate_country_to_code(region)
    packages = scraper_logic.get_package_by_name(app_name, region=region_code)
    if packages:
        return {"package_id": packages[0]}
    return {"package_id": None}

@app.get("/api/app-details")
def app_details(package_id: str, region: str = "US"):
    region_code = scraper_logic.translate_country_to_code(region)
    details = scraper_logic.get_app_details(package_id, region=region_code)
    if not details:
        raise HTTPException(status_code=404, detail="App not found")
    return details
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)