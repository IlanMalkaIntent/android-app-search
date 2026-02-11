# main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google import genai
import scraper_logic

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class SearchRequest(BaseModel):
    topic: str
    region: str
    resolve_pkg_with_ai: bool = False
    api_key: str
    model_name: str

@app.get("/")
def read_root():
    return FileResponse('static/index.html')

@app.post("/api/search")
def search_apps(request: SearchRequest):
    try:
        # Initialize Client dynamically
        client = genai.Client(api_key=request.api_key)
        print(f" Starting search for topic: {request.topic} in region: {request.region} using model: {request.model_name}")
        
        # 1. Get initial list
        raw_results = scraper_logic.get_market_research(
            request.topic, 
            request.region, 
            client, 
            request.model_name
        )
        
        # 2. Process and verify
        final_results = scraper_logic.process_results(
            raw_results, 
            request.region, 
            request.resolve_pkg_with_ai, 
            client,
            request.model_name
        )
        
        return {"data": final_results}
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
def verify_package(package_name: str, app_name: str = ""):
    exists = scraper_logic.verify_package_exists(package_name)
    if exists:
        return {
            "status": "Verified",
            "play_store_url": f"https://play.google.com/store/apps/details?id={package_name}"
        }
    else:
        return {
            "status": "Not Found",
            "play_store_url": f"https://play.google.com/store/search?q={app_name}&c=apps"
        }

@app.get("/api/find-package")
def find_package(app_name: str):
    """
    Attempts to find a package ID for a given app name.
    Returns the first matching package ID or None.
    """
    packages = scraper_logic.get_package_by_name(app_name)
    if packages:
        return {"package_id": packages[0]}
    return {"package_id": None}

@app.get("/api/app-details")
def app_details(package_id: str):
    details = scraper_logic.get_app_details(package_id)
    if not details:
        raise HTTPException(status_code=404, detail="App not found")
    return details
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)