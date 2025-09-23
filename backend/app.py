from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, AnyHttpUrl
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import io, base64, qrcode, random, string

from db import SessionLocal, init_db
from models import Link

app = FastAPI(title="Shorty+QR")
init_db()

# Allow everything for now (simplify local testing). Tighten later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def create_link(payload: CreateLink):
    with SessionLocal() as db:
        slug = payload.customSlug or generate_slug()
        # Ensure slug is unique; if collision, try a few times
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

        # Optional: Return a data-URL QR image (handy for testing)
        # We'll encode the redirect URL (host will be added in the frontend later).
        qr_data = f"/r/{link.slug}"
        img = qrcode.make(qr_data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        dataurl = "data:image/png;base64," + base64.b64encode(buf.read()).decode()

        return {
            "id": link.id,
            "slug": link.slug,
            "url": link.url,
            "clicks": link.clicks,
            "qrPng": dataurl
        }

@app.get("/api/links")
def list_links(limit: int = 50, offset: int = 0):
    with SessionLocal() as db:
        total = db.query(Link).count()
        items = db.query(Link).order_by(Link.id.desc()).offset(offset).limit(limit).all()
        return {"items": [l.to_dict() for l in items], "total": total}

@app.get("/api/links/{slug}")
def get_link(slug: str):
    with SessionLocal() as db:
        l = db.scalar(select(Link).where(Link.slug == slug))
        if not l:
            raise HTTPException(404, "Not found")
        return l.to_dict()

@app.delete("/api/links/{id}", status_code=204)
def delete_link(id: int):
    with SessionLocal() as db:
        l = db.get(Link, id)
        if not l:
            raise HTTPException(404, "Not found")
        db.delete(l)
        db.commit()
        return

@app.get("/api/links/{slug}/qr")
def qr(slug: str, request: Request):
    # Build a full redirect URL (e.g., http://localhost:8080/r/abc123)
    base = str(request.base_url).rstrip("/")
    full_url = f"{base}/r/{slug}"
    img = qrcode.make(full_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.get("/r/{slug}")
def redirect(slug: str):
    with SessionLocal() as db:
        l = db.scalar(select(Link).where(Link.slug == slug))
        if not l:
            raise HTTPException(404, "Not found")
        l.clicks += 1
        db.add(l)
        db.commit()
        return RedirectResponse(l.url, status_code=302)
