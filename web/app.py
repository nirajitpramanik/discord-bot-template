"""
Web interface for the Discord bot
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from config.settings import Settings
from database.database import Database

logger = logging.getLogger(__name__)

def create_web_app() -> FastAPI:
    """Create and configure the FastAPI web application"""
    
    settings = Settings()
    
    app = FastAPI(
        title="Discord Bot Web Interface",
        description="Web interface for managing the Discord bot",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else settings.ALLOWED_DOMAINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Initialize database
    database = Database()
    
    # Security
    security = HTTPBearer(auto_error=False)
    
    # Templates (if using HTML templates)
    templates = None
    if os.path.exists("web/templates"):
        templates = Jinja2Templates(directory="web/templates")
    
    # Static files
    if os.path.exists("web/static"):
        app.mount("/static", StaticFiles(directory="web/static"), name="static")
    
    # Dependency to verify API key
    async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
        if not credentials:
            return False
        
        api_key = os.getenv('WEB_API_KEY')
        if not api_key:
            return settings.DEBUG  # Allow access in debug mode if no API key set
        
        return credentials.credentials == api_key
    
    # Routes
    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Root endpoint"""
        if templates:
            return templates.TemplateResponse("index.html", {"request": request})
        
        return HTMLResponse("""
        <html>
            <head><title>Discord Bot</title></head>
            <body>
                <h1>Discord Bot Web Interface</h1>
                <p>Bot is running!</p>
                <p><a href="/health">Health Check</a></p>
                <p><a href="/stats">Statistics</a></p>
                <p><a href="/docs">API Documentation</a> (if enabled)</p>
            </body>
        </html>
        """)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            # Check database connection
            db_status = await database.get_health_status()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": db_status,
                "version": "1.0.0"
            }
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
            )
    
    @app.get("/stats")
    async def get_stats(authorized: bool = Depends(verify_api_key)):
        """Get bot statistics"""
        if not authorized:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        try:
            # Get basic stats
            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": "N/A",  # Would need to track bot start time
                "guilds": 0,      # Would need bot instance
                "users": 0,       # Would need bot instance
                "commands_used": 0,  # Would need to track in database
                "database": await database.get_health_status()
            }
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.get("/api/guilds")
    async def get_guilds(authorized: bool = Depends(verify_api_key)):
        """Get bot guild information"""
        if not authorized:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # This would require access to the bot instance
        # For now, return placeholder data
        return {
            "guilds": [],
            "total": 0,
            "message": "Bot instance not accessible from web interface"
        }
    
    @app.post("/api/command")
    async def execute_command(
        command_data: Dict[str, Any],
        authorized: bool = Depends(verify_api_key)
    ):
        """Execute a bot command via API"""
        if not authorized:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # This would require implementing a command queue system
        # to communicate with the bot instance
        return {
            "status": "not_implemented",
            "message": "Command execution via web interface not implemented"
        }
    
    @app.get("/api/logs")
    async def get_logs(
        lines: int = 100,
        level: str = "INFO",
        authorized: bool = Depends(verify_api_key)
    ):
        """Get recent log entries"""
        if not authorized:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        try:
            log_file = settings.LOG_FILE
            if not os.path.exists(log_file):
                return {"logs": [], "message": "Log file not found"}
            
            # Read last N lines from log file
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            
            # Filter by log level if specified
            if level != "ALL":
                filtered_lines = [line for line in recent_lines if f"[{level}]" in line]
                recent_lines = filtered_lines
            
            return {
                "logs": [line.strip() for line in recent_lines],
                "total_lines": len(recent_lines),
                "log_file": log_file
            }
        
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            raise HTTPException(status_code=500, detail="Failed to read logs")
    
    @app.get("/api/config")
    async def get_config(authorized: bool = Depends(verify_api_key)):
        """Get bot configuration (non-sensitive parts)"""
        if not authorized:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        return {
            "prefix": settings.DEFAULT_PREFIX,
            "debug": settings.DEBUG,
            "features": {
                "web_interface": settings.ENABLE_WEB_INTERFACE,
                "crawler": settings.ENABLE_CRAWLER,
                "logging": settings.ENABLE_LOGGING
            },
            "limits": {
                "global_rate_limit": settings.GLOBAL_RATE_LIMIT,
                "user_rate_limit": settings.USER_RATE_LIMIT,
                "cache_ttl": settings.CACHE_TTL
            }
        }
    
    # Error handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={"error": "Not found", "path": str(request.url.path)}
        )
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        logger.error(f"Internal server error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    
    # Lifecycle events
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup"""
        logger.info("Starting web interface...")
        await database.initialize()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("Shutting down web interface...")
        await database.close()
    
    return app