from apps.api.auth import UserSession, get_current_user_session
from apps.api.routers import audits, patches
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="DPDP 360° AI Compliance Auditor API",
    description="FastAPI gateway for the DPDP 360° AI Compliance Auditor",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(audits.router)
app.include_router(patches.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "status": "online",
        "service": "DPDP 360° AI Compliance Auditor Gateway",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/auth/me")
async def get_current_session(
    session: UserSession = Depends(get_current_user_session),
) -> dict[str, str | None]:
    """Protected endpoint returning the authenticated user's session and organization scope."""
    return {
        "user_id": session.user_id,
        "organization_id": session.organization_id,
        "role": session.role,
        "email": session.email,
    }
