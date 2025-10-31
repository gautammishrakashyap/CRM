from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from app.core.exceptions import http_error_handler, http422_error_handler
from app.api.routes import router as api_router
from app.core.config import ALLOWED_HOSTS, DEBUG, PROJECT_NAME, VERSION
from app.core.database import create_start_app_handler, create_stop_app_handler


def get_application() -> FastAPI:
    application = FastAPI(
        title=PROJECT_NAME, 
        debug=DEBUG, 
        version=VERSION,
        openapi_tags=[
            {
                "name": "Authentication",
                "description": "🔐 Login and token management - get Bearer tokens for API access"
            },
            {
                "name": "USER V1",
                "description": "👤 User management and profile endpoints"
            },
            {
                "name": "ADMIN V1", 
                "description": "🛡️ Admin endpoints - roles, permissions, and user management"
            },
            {
                "name": "STUDENT V1",
                "description": "🎓 Student profile management - create and manage student profiles, qualifications, and preferences"
            }
        ]
    )

    # Event handlers
    application.add_event_handler("startup", create_start_app_handler(application))
    application.add_event_handler("shutdown", create_stop_app_handler(application))

    # Exception handlers
    application.add_exception_handler(HTTPException, http_error_handler)
    application.add_exception_handler(RequestValidationError, http422_error_handler)

    # Routers
    application.include_router(api_router)

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


app = get_application()


# # Optional: run directly with `uv run python app/api/main.py`
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
