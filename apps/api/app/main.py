from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import SessionLocal, engine
from app.deps import get_ai
from app.errors import install_error_handlers
from app.models import Base
from app.routers import admin, bookings, chat, contact, mentor_link, mentors, students
from app.seed import seed_all


def create_app() -> FastAPI:
    app = FastAPI(title="Mentor Connect API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)

    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health() -> dict[str, bool | str]:
        return {"ok": True, "ai": get_ai().mode}

    for module in (mentors, students, chat, bookings, mentor_link, admin, contact):
        api.include_router(module.router)
    app.include_router(api)

    # Tables and seed data are ready as soon as the app exists, with or without a startup event.
    # Skipped when AUTO_SETUP=0 so parallel cold starts on a shared database do not race.
    if get_settings().auto_setup:
        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            report = seed_all(db)
        if report:
            print(report.format())
    return app


app = create_app()
