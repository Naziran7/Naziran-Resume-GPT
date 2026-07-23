from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.resumes import router as resumes_router
from app.api.v1.endpoints.chatbot import router as chatbot_router

api_router = APIRouter()

# Register sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(chatbot_router, prefix="/chatbot", tags=["chatbot"])

@api_router.get("/health", tags=["health"])
async def health_check():
    """Verify application health and connectivity."""
    return {"status": "healthy", "service": "NaziranGPT API"}
