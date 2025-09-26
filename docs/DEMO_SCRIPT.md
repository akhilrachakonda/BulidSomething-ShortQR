# Demo Script

Use this outline to record the required 5–10 minute walkthrough for the assignment.

---

### 1. Introduction (1 minute)
- State the goal: “Shorty+QR is a Kubernetes-deployed URL shortener with QR code generation.”
- Mention the four workloads (frontend, url-service, qr-service, postgres) and that each backend scales via HPAs.

### 2. Show the Cluster State (1 minute)
```bash
kubectl get pods -n shorty
kubectl get svc -n shorty
kubectl get hpa -n shorty
```
- Call out that the Postgres service is backed by a PVC (show `kubectl get pvc -n shorty`).

### 3. Access Through the Ingress (1 minute)
- Start `sudo minikube tunnel` beforehand.
- In the video, open `https://shorty.local/` and accept the self-signed certificate.
- Point out the three ingress paths (`/`, `/api`, `/api/qr`) in `kubernetes/ingress.yaml`.

### 4. Create and Use a Short Link (2 minutes)
- In the UI, submit a long URL.
- Show the REST call in the browser dev tools or with `curl -sk https://shorty.local/api/links`.
- Demonstrate the redirect: `https://shorty.local/r/<slug>`.
- Display the click counter increment (refresh the list or run `curl -sk https://shorty.local/api/links | jq`).

### 5. Generate a QR Code (1 minute)
- Click the QR button in the UI to render the PNG served by `qr-service`.
- Optionally, download via `curl -sk https://shorty.local/api/qr?slug=<slug> -o qr.png` and show the file type (`file qr.png`).

### 6. Logs and Scaling (2 minutes)
```bash
kubectl logs deployment/url-service -n shorty --tail=10
kubectl logs deployment/qr-service -n shorty --tail=10
```
- Explain how HPAs (`url-service-hpa`, `qr-service-hpa`) observe CPU usage and expand replicas. Mention how to generate load if you want to demonstrate scaling.

### 7. YAML Tour & Security Notes (1 minute)
- Highlight key sections of the manifests:
  - `kubernetes/url-service-deployment.yaml` (env vars from Secret, probes, resources).
  - `kubernetes/postgres-pvc.yaml` (persistent storage).
  - `kubernetes/ingress.yaml` (annotations disabling forced TLS redirect for local dev).
- Reference `SECURITY.md` for future hardening steps (TLS from cert-manager, NetworkPolicies, etc.).

### 8. Wrap-Up (under 1 minute)
- Summarize the business value (campaign links + QR codes, independent scaling, reliable persistence).
- Point to the repository URL and note that the Docker images are published to Docker Hub.
- End with the next steps (production hardening, monitoring, etc.).
