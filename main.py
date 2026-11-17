from fastapi import FastAPI
from contextlib import asynccontextmanager
from controllers import (
    AuthController, UserController, 
    HealthController, CourseController, 
    ModuleController, JobApplicationController,
    AIController, ProfessionController, PolicyController
)
from middleware.logger import LoggingMiddleware
from utils.logger import setup_logging, get_logger
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

setup_logging()
logger = get_logger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("FastAPI application starting up...")
    # Note: Database tables are now managed by Alembic migrations
    # Run 'alembic upgrade head' to create/update tables
    logger.info("Application startup complete!")
    yield
    # Shutdown
    logger.info("FastAPI application shutting down...")


def create_app() -> FastAPI:
    app_meta = {
        "title": "Career Elevate",
        "description": "Career Elevate Backend API",
        "version": "1.0.0",
        "lifespan": lifespan
    }
    # Create FastAPI app
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    if ENVIRONMENT == "development":
        app = FastAPI(**app_meta)
    else:
        app = FastAPI(
            **app_meta,
            docs_url=None,
            redoc_url=None,
            openapi_url=None 
        )

    # Add Logging middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("CORS_ORIGIN"), "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["POST", "GET", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    
    # Trust proxy headers from nginx for proper HTTPS redirects
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
    
    # Initialize controllers
    user_controller = UserController()
    health_controller = HealthController()
    auth_controller = AuthController()
    course_controller = CourseController()
    module_controller = ModuleController()
    job_application_controller = JobApplicationController()
    ai_controller = AIController()
    profession_controller = ProfessionController()
    policy_controller = PolicyController()

    # Include routers
    app.include_router(user_controller.router)
    app.include_router(health_controller.router)
    app.include_router(auth_controller.router)
    app.include_router(course_controller.router)
    app.include_router(module_controller.router)
    app.include_router(job_application_controller.router)
    app.include_router(ai_controller.router)
    app.include_router(profession_controller.router)
    app.include_router(policy_controller.router)

    return app

app = create_app()


if __name__ == "__main__":
    logger.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)