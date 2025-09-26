# Shorty+QR

Shorty+QR is a microservice-based URL shortener with QR code generation. The system is designed to showcase independent microservices, a persistent database, and Kubernetes-first deployment practices that satisfy the course assignment requirements.

---

GitHub repository (public): https://github.com/akhilrachakonda/BulidSomething-ShortQR

All Kubernetes manifests in `kubernetes/` match the demo deployment and can be applied directly with `kubectl apply -f kubernetes/`.

## 1. What the Software Does
- Accepts long URLs, returns shortened slugs, keeps click counts, and redirects visitors to the original address.
- Generates QR codes for any stored slug so real-world campaigns can distribute scannable links.
- Presents a React single-page interface that drives the workflow through REST calls; the same APIs can be exercised directly with `curl` or any HTTP client.

| Endpoint | Method | Service | Description |
| --- | --- | --- | --- |
| `/api/links` | `POST`, `GET` | url-service | Create or list short links |
| `/api/links/{id}` | `DELETE` | url-service | Remove an existing link |
| `/r/{slug}` | `GET` | url-service | Redirect to the original URL & increment click counter |
| `/api/qr?slug={slug}` | `GET` | qr-service | Stream the QR PNG bytes |
| `/healthz` | `GET` | all services | Liveness/readiness endpoint |

---

## 2. Microservices & Responsibilities
- **frontend** (React + Nginx)
  - Delivers the SPA, calls REST APIs, renders QR images.
  - Configured for zero state; can scale horizontally without coordination.
- **url-service** (FastAPI, SQLAlchemy, SlowAPI)
  - Owns link CRUD, redirects, click counters, and rate limiting.
  - Persists data to Postgres through SQLAlchemy sessions.
- **qr-service** (FastAPI, qrcode)
  - Stateless QR generator that returns PNG streams. Shares the same ConfigMap as url-service for allowed origins/base URL.
- **postgres** (Deployment + PVC)
  - Stores URLs, slugs, and click metrics. Uses a dedicated PersistentVolumeClaim so data outlives pod restarts.

Kubernetes ConfigMaps and Secrets provide environment values (`shortyqr-config`, `postgres-secret`). Horizontal Pod Autoscalers (`url-service-hpa`, `qr-service-hpa`) keep each stateless backend independently scalable between 2 and 5 replicas.

---

## 3. Architecture & Design Principles
- **Ingress Gateway Pattern**: A single NGINX ingress exposes the app externally and routes by path: `/` to the frontend, `/api` & `/r` to url-service, `/api/qr` & `/qr` to qr-service.
- **Stateless Workloads**: Each Python service avoids local disk state; all persistence lives in PostgreSQL. Scaling and rolling upgrades are therefore straightforward.
- **Config/Secret Decoupling**: The twelve-factor "store config in the environment" principle is applied with ConfigMaps (public settings) and Secrets (credentials).
- **Autoscaling**: HPAs monitor CPU usage and adjust replicas for url-service and qr-service, demonstrating independent horizontal scalability.
- **Persistent Storage**: A PVC binds to the Postgres deployment, guaranteeing data survives node or pod churn.

For a deeper narrative, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), which maps each component, details traffic flow, and explains the microservice split.

---

## 4. Benefits, Challenges, and Security Considerations
### Benefits
- **Independent Scaling**: QR generation and core URL operations scale separately, matching their resource profiles.
- **Resilience**: Failures in qr-service never block redirects; Kubernetes probes and HPAs restore capacity automatically.
- **Extensibility**: Each microservice can evolve in isolation (e.g., swap qr-service implementation without touching url-service).

### Challenges & Mitigations
- **Ingress TLS vs. HTTP**: Minikube ships a self-signed certificate; when testing locally you must accept it or use `curl -k`. In production, terminate TLS with a trusted certificate (e.g., cert-manager + Let’s Encrypt).
- **Network Policies**: Strict policies can break ingress traffic if DNS or controller IPs are not allowed. The provided manifests leave policies disabled by default and document how to re-enable them gradually (see `docs/SECURITY.md`).
- **State Management**: Only the database is stateful; ensure backups and monitoring are in place. PVC size is currently `1Gi`—adjust for production workloads.

### Security Highlights
- Secrets live in `postgres-secret` and are never baked into images.
- Containers run as non-root with hardened base images.
- Rate limiting via SlowAPI protects link creation and listing from brute-force misuse.
- CORS is restricted to `shorty.local` origins; adjust as required for deployment domains.
- `docs/SECURITY.md` lists additional hardening ideas (TLS, network policies, WAF, etc.).

---

## 5. Deploying on Minikube
1. **Prerequisites**: Docker, kubectl, minikube, Node.js (for optional frontend dev).
2. **Start minikube & addons**
   ```bash
   minikube start
   minikube addons enable ingress
   minikube addons enable metrics-server
   ```
3. **Build & push images** (or reuse the published images under `akhilrachakonda2004347/shortyqr-*`).
   ```bash
   docker build -t <dockerhub-user>/shortyqr-frontend:latest frontend
   docker push <dockerhub-user>/shortyqr-frontend:latest
   # Repeat for backend/url-service and backend/qr-service
   ```
   Update the image references in `kubernetes/*.yaml` if you publish under a different account.
4. **Configure secrets**
   ```bash
   kubectl apply -f kubernetes/postgres-secret.yaml
   ```
   (Edit the password before applying; do **not** commit real credentials.)
5. **Apply the manifests**
   ```bash
   kubectl apply -f kubernetes/
   ```
6. **Expose the ingress**
   ```bash
   sudo minikube tunnel   # keep this terminal open
   ```
7. **Map the hostname**
   ```bash
   echo "127.0.0.1 shorty.local" | sudo tee -a /etc/hosts
   ```
8. **Access the app**
   - Visit `https://shorty.local/` in your browser. Accept the self-signed certificate when prompted.
   - API test:
     ```bash
     curl -sk https://shorty.local/api/links
     ```

> **Tip**: If you prefer plain HTTP, restart `minikube tunnel`, reapply `kubernetes/ingress.yaml`, and use `http://shorty.local`. Self-signed TLS is enabled by default to satisfy security best practices.

---

## 6. Operational Notes
- **Scaling**: `kubectl get hpa -n shorty` shows live scaling targets. Adjust `minReplicas`, `maxReplicas`, or CPU utilization thresholds in the HPA manifests.
- **Logs & Debugging**
  ```bash
  kubectl logs deployment/url-service -n shorty
  kubectl logs deployment/qr-service -n shorty
  kubectl logs deployment/frontend -n shorty
  ```
- **Database Access**
  ```bash
  kubectl port-forward svc/postgres-svc -n shorty 5432:5432
  psql postgresql://postgres:<password>@localhost:5432/shortyqr
  ```

---

## 7. Testing & Local Development
- **Frontend**
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
- **URL service**
  ```bash
  cd backend/url-service
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  pytest
  uvicorn app:app --reload --port 8080
  ```
- **QR service**
  ```bash
  cd backend/qr-service
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  uvicorn app:app --reload --port 8081
  ```

---
