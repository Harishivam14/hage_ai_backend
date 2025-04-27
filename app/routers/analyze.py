# app/routers/analyze.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional, List
import os
from datetime import datetime
import json

from app.services import instagram, youtube
from app.services.comment_analyzer import analyze_comments
from app.utils.file_manager import save_output_files
from app.utils.url_parser import get_platform_from_url

router = APIRouter(prefix="/api", tags=["analyze"])

# In-memory storage for tracking analysis jobs
analysis_jobs = {}

# Request/Response Models
class URLRequest(BaseModel):
    url: HttpUrl
    
class AnalysisResponse(BaseModel):
    request_id: str
    status: str = "processing"
    file_urls: Optional[Dict[str, str]] = None
    error: Optional[str] = None

# Background task to process URLs
async def process_url(request_id: str, url: str):
    try:
        # Determine platform from URL
        platform = get_platform_from_url(url)
        
        if platform == "Instagram":
            comments, metadata = await instagram.extract_metadata(url)
        elif platform == "YouTube":
            comments, metadata = await youtube.extract_data(url)
        else:
            analysis_jobs[request_id] = {
                "status": "failed",
                "error": "Unsupported URL. Only Instagram and YouTube are supported."
            }
            return
        
        # If we have comments, perform advanced analysis
        if comments:
            # Run the comment analyzer
            analysis_results = await analyze_comments(comments)
            
            # Update comments with enriched data from analysis
            if "processed_comments" in analysis_results:
                comments = analysis_results["processed_comments"]
            
            # Add insights to metadata
            if "insights" in analysis_results:
                metadata["Insights"] = analysis_results["insights"]
            
            # Add aspect summaries to metadata
            if "aspect_summaries" in analysis_results:
                metadata["AspectSummaries"] = analysis_results["aspect_summaries"]
        
        # Save files
        file_urls = save_output_files(request_id, comments, metadata, platform)
        
        # Save insights as JSON file
        if comments and "insights" in metadata:
            insights_file = f"{platform.lower()}_insights_{request_id}.json"
            insights_path = os.path.join("output", file_urls.get("folder", ""), insights_file)
            
            with open(insights_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.get("Insights", {}), f, indent=2)
            
            file_urls["insights_json"] = f"/api/files/{file_urls.get('folder', '')}/{insights_file}"
        
        # Update job status
        analysis_jobs[request_id] = {
            "status": "completed",
            "file_urls": file_urls,
            "comment_count": len(comments),
            "platform": platform,
            "folder": file_urls.get("folder", "")
        }
        
    except Exception as e:
        analysis_jobs[request_id] = {
            "status": "failed",
            "error": str(e)
        }

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_url(url_request: URLRequest, background_tasks: BackgroundTasks):
    """Submit a URL for analysis"""
    request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(3).hex()}"
    
    # Start background processing
    background_tasks.add_task(process_url, request_id, str(url_request.url))
    
    # Return request ID for status checking
    return AnalysisResponse(
        request_id=request_id,
        status="processing"
    )

@router.get("/status/{request_id}", response_model=AnalysisResponse)
async def check_status(request_id: str):
    """Check the status of a submitted URL analysis"""
    if request_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    job = analysis_jobs[request_id]
    
    response = AnalysisResponse(
        request_id=request_id,
        status=job.get("status", "processing")
    )
    
    if "file_urls" in job:
        response.file_urls = job["file_urls"]
    
    if "error" in job:
        response.error = job["error"]
    
    return response