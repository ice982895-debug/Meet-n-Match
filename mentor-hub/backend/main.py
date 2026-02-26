import os
import json
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import your custom logic
from mentor_matching_system import MentorMatchingSystem
from database import engine, Base
from auth import router as auth_router

# --- Lifespan Logic ---
# This replaces @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Everything before 'yield' runs on Startup.
    Everything after 'yield' runs on Shutdown.
    """
    # 1. Startup: Load data and train the model
    try:
        Base.metadata.create_all(bind=engine) # Create DB tables
        base_dir = os.path.dirname(os.path.abspath(__file__))
        mentors_path = os.path.join(base_dir, "mentors.json")
        
        if os.path.exists(mentors_path):
            with open(mentors_path, "r") as f:
                mentors_data = json.load(f)
            
            matcher.load_mentors(mentors_data)
            matcher.train()
            print(f"✅ Loaded {len(mentors_data)} mentors and trained model.")
        else:
            print(f"⚠️ Warning: {mentors_path} not found. Model not trained.")
            
    except Exception as e:
        print(f"❌ Error during startup: {e}")
    
    yield  # --- The App is now running ---

    # 2. Shutdown: Clean up resources
    print("🛑 Shutting down MentorHub API...")

# --- Global Instance ---
matcher = MentorMatchingSystem()

# --- App Initialization ---
app = FastAPI(title="MentorHub API", lifespan=lifespan)

app.include_router(auth_router, prefix="/auth", tags=["auth"])

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class MenteeProfile(BaseModel):
    job_title: str
    tools: List[str]
    years_of_experience: int
    interests: List[str]
    bio: str

class MentorMatch(BaseModel):
    user_id: str
    job_title: str
    years_of_experience: int
    match_score: float
    bio: str
    tools: List[str]
    interests: List[str]

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "MentorHub API is running"}

@app.get("/api/meta")
async def get_metadata(job_title: Optional[str] = None):
    """Returns available options for frontend dropdowns."""
    if not matcher.is_trained:
        raise HTTPException(status_code=503, detail="Model not trained yet.")
    
    if job_title:
        return {
            "job_titles": matcher.get_all_job_titles(), 
            "tools": matcher.get_related_tools(job_title),
            "interests": matcher.get_related_interests(job_title)
        }
        
    return {
        "job_titles": matcher.get_all_job_titles(),
        "tools": matcher.get_all_tools(),
        "interests": matcher.get_all_interests()
    }

@app.post("/api/match", response_model=List[MentorMatch])
async def find_matches(profile: MenteeProfile):
    """Calculates top matches using TF-IDF."""
    if not matcher.is_trained:
         raise HTTPException(status_code=503, detail="Model not trained yet.")
    
    profile_dict = profile.dict()
    matches = matcher.get_matches(profile_dict, top_n=5)
    return matches

@app.get("/api/mentors")
async def get_mentors(
    page: int = 1, 
    limit: int = 12, 
    tool: Optional[str] = None, 
    interest: Optional[str] = None
):
    """Paginated directory of mentors."""
    if not matcher.is_trained:
        raise HTTPException(status_code=503, detail="Model not trained yet.")
        
    mentors, total = matcher.get_mentors(page, limit, tool_filter=tool, interest_filter=interest)
    
    return {
        "data": mentors,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }