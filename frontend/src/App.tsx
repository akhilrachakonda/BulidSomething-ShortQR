import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

type Link = { id:number; slug:string; url:string; clicks:number; createdAt?:string };

const RAW_API_BASE = (import.meta.env.VITE_API_BASE || '').trim();
const API_BASE = (() => {
  if (!RAW_API_BASE) return '';
  try {
    const candidate = new URL(RAW_API_BASE, window.location.origin);
    if (window.location.protocol === 'https:' && candidate.protocol === 'http:') {
      return `${window.location.origin}${candidate.pathname === '/' ? '' : candidate.pathname}`;
    }
    return candidate.toString();
  } catch {
    return RAW_API_BASE;
  }
})();
const api = axios.create({ baseURL: API_BASE || undefined });

function enrichLink(link: Link) {
  const origin = window.location.origin;
  const shortUrl = `${origin}/r/${link.slug}`;
  const qrCodeUrl = `${API_BASE}/api/qr?slug=${link.slug}`;
  return { ...link, shortUrl, qrCodeUrl };
}

export default function App() {
  const [url, setUrl] = useState("");
  const [links, setLinks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedSlug, setCopiedSlug] = useState<string | null>(null);
  const [activeLink, setActiveLink] = useState<any | null>(null);
  const [view, setView] = useState<"form" | "qr">("form");

  async function loadLinks() {
    try {
      const res = await api.get("/api/links");
      setLinks((res.data.items ?? []).map(enrichLink));
    } catch (e:any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to load links");
    }
  }

  useEffect(() => { loadLinks(); }, []);

  async function createLink(e: React.FormEvent) {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/api/links", { url });
      setUrl("");
      await loadLinks();
      setActiveLink(enrichLink(res.data));
      setView("qr");
    } catch (e:any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to create link");
    } finally {
      setLoading(false);
    }
  }

  async function deleteLink(id:number) {
    try {
      await api.delete(`/api/links/${id}`);
      await loadLinks();
    } catch (e:any) {
      setError(e?.response?.data?.detail || e?.message || "Failed to delete link");
    }
  }

  function copyToClipboard(slug: string) {
    const shortUrl = `${window.location.origin}/r/${slug}`;
    navigator.clipboard.writeText(shortUrl).then(() => {
      setCopiedSlug(slug);
      setTimeout(() => setCopiedSlug(null), 2000); // Reset after 2 seconds
    });
  }

  if (view === "qr" && activeLink) {
    return (
      <div className="app-root qr-view">
        <div className="container">
          <img src={activeLink.qrCodeUrl} alt={`QR code for ${activeLink.slug}`} className="qr-code-full" />
          <p><a href={activeLink.shortUrl} target="_blank" rel="noopener noreferrer">{activeLink.shortUrl}</a></p>
          <button onClick={() => setView("form")} className="back-button">Back</button>
        </div>
      </div>
    );
  }

  return (
    <div className="app-root">
      <header className="section section-header">
        <div className="container">
          <h1>Shorty+QR</h1>
          <p>A simple, modern URL shortener.</p>
        </div>
      </header>

      <section className="section section-form">
        <div className="container">
          <form onSubmit={createLink} className="form-container">
            <input
              type="url"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="Paste a long URL (e.g., https://...)"
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Shorten"}
            </button>
          </form>
          {error && <p className="error-message">{error}</p>}
        </div>
      </section>

      <main className="section section-links">
        <div className="container">
          <div className="links-container">
            {links.map(link => (
              <div key={link.id} className="link-card">
                <div className="link-info">
                  <p className="original-url" title={link.url}>{link.url}</p>
                  <div className="short-url-container">
                    <a href={link.shortUrl} target="_blank" rel="noopener noreferrer" className="short-url">
                      {link.shortUrl.replace(/https?:\/\//, '')}
                    </a>
                    <button onClick={() => copyToClipboard(link.slug)} className="copy-button">
                      {copiedSlug === link.slug ? "Copied!" : "Copy"}
                    </button>
                  </div>
                  <div className="link-stats">
                    <span>Clicks: <strong>{link.clicks}</strong></span>
                    <button onClick={() => deleteLink(link.id)} className="delete-button" title="Delete">✕</button>
                  </div>
                </div>
                <div className="qr-code">
                  <img src={link.qrCodeUrl} alt={`QR code for ${link.slug}`} />
                </div>
              </div>
            ))}
            {links.length === 0 && !loading && <p className="empty-state">No links yet. Create one above!</p>}
          </div>
        </div>
      </main>
    </div>
  );
}