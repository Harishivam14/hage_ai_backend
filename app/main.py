from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uvicorn

from app.routers import analyze
from app.routers import llm_router

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Social Media Comment Analyzer",
    description="API for extracting and analyzing comments from Instagram and YouTube",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files directory for serving output files
app.mount("/api/files", StaticFiles(directory="output"), name="output")

# Include routers
app.include_router(analyze.router)
app.include_router(llm_router.router)

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Social Media Comment Analyzer API",
        "documentation": "/docs",
        "redoc": "/redoc"
    }
    
# if __name__ == "__main__":
#     uvicorn.run("app.main:app", host="127.0.0.1", port=7000)