from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, AnyHttpUrl
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import os, random, string
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from db import SessionLocal, init_db
from models import Link

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="URL Shortener Service")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

init_db()

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://shorty.local").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CreateLink(BaseModel):
    url: AnyHttpUrl
    customSlug: str | None = None

def generate_slug(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/api/links")
@limiter.limit("100/minute")
def create_link(payload: CreateLink, request: Request):
    with SessionLocal() as db:
        slug = payload.customSlug or generate_slug()
        tries = 0
        while db.scalar(select(Link).where(Link.slug == slug)) is not None:
            slug = generate_slug()
            tries += 1
            if tries > 5:
                raise HTTPException(500, "Could not generate unique slug")
        link = Link(slug=slug, url=str(payload.url))
        db.add(link)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Slug already exists")
        db.refresh(link)
        return link.to_dict()

@app.get("/api/links")
@limiter.limit("100/minute")
def list_links(request: Request, limit: int = 50, offset: int = 0):
    with SessionLocal() as db:
        total = db.query(Link).count()
        items = db.query(Link).order_by(Link.id.desc()).offset(offset).limit(limit).all()
        return {
            "items": [l.to_dict() for l in items],
            "total": total,
        }

@app.get("/api/links/{slug}")
@limiter.limit("100/minute")
def get_link(slug: str, request: Request):
    with SessionLocal() as db:
        l = db.scalar(select(Link).where(Link.slug == slug))
        if not l:
            raise HTTPException(404, "Not found")
        return l.to_dict()

@app.delete("/api/links/{id}", status_code=204)
@limiter.limit("100/minute")
def delete_link(id: int, request: Request):
    with SessionLocal() as db:
        l = db.get(Link, id)
        if not l:
            raise HTTPException(404, "Not found")
        db.delete(l)
        db.commit()
        return

@app.get("/r/{slug}")
def redirect_to_url(slug: str):
    with SessionLocal() as db:
        l = db.scalar(select(Link).where(Link.slug == slug))
        if not l:
            raise HTTPException(404, "Not found")
        l.clicks += 1
        db.add(l)
        db.commit()
        return RedirectResponse(l.url, status_code=302)

