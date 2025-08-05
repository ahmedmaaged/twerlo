from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import time

from app.database.mongodb import connect_to_mongo, close_mongo_connection
from app.database.qdrant_client import connect_to_qdrant, close_qdrant_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up Twerlo API...")
    await connect_to_mongo()
    connect_to_qdrant()
    yield
    # Shutdown
    print("Shutting down Twerlo API...")
    await close_mongo_connection()
    close_qdrant_connection()

app = FastAPI(
    title="Twerlo AI-Powered Q&A API",
    description="A simple AI-powered question-answering API service using LLM and vector database",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
templates = Jinja2Templates(directory="app/templates")

# Root redirect to HTML index
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Include routers
from app.endpoints import ask, auth, documents
app.include_router(auth.router, tags=["Authentication"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(ask.router, tags=["Ask"])
