# Security Overview

This document captures the current security posture of the `shortyqr` project and highlights areas for improvement.

## Secrets & Configuration
- Database credentials live in a Kubernetes Secret (`postgres-secret`). Deployment manifests consume the values through `envFrom`/`secretKeyRef` so credentials never appear in images.
- Configurable values (allowed origins, public base URL) are stored in the `shortyqr-config` ConfigMap. Update once and redeploy to apply across services.
- **Recommendation**: Generate strong unique passwords per environment and create the secret dynamically (`kubectl create secret ...`) instead of storing the YAML in version control.

## Container Hardening
- Backend and frontend containers run as non-root users (`runAsUser: 1000`, `allowPrivilegeEscalation: false`).
- Images are built from slim Alpine/Debian bases to reduce package surface area.
- Health probes and resource limits are defined for every deployment to keep unhealthy containers out of rotation and avoid noisy-neighbor issues.

## Application-Level Protections
- The `url-service` validates incoming URLs with Pydantic and enforces rate limits via SlowAPI (`100/minute`).
- CORS is restricted to `shorty.local` and `shorty.local:8080` by default. Adjust the ConfigMap when deploying to other domains.
- QR generation is stateless; errors there do not expose database contents.

## Network & Transport
- The manifests currently leave NetworkPolicies disabled to keep ingress traffic straightforward in minikube. Earlier iterations showed 502s when DNS and ingress-controller ranges were blocked. If you re-enable policies, add rules that:
- In production the Ingress should terminate HTTPS with a trusted certificate. The recommended path is cert-manager issuing Let’s Encrypt certificates so browsers trust the domain automatically.
  - Allow ingress from the `ingress-nginx` namespace to all app pods.
  - Permit egress from workloads to kube-dns (UDP/TCP 53) and any downstream service they need (postgres, qr-service).
- External traffic is served over HTTPS by default; minikube uses a self-signed certificate. Accept it locally or install a trusted cert (e.g., via cert-manager + Let’s Encrypt) in production.
- Internal service-to-service traffic is plaintext inside the cluster. Adopt mTLS (service mesh) if regulatory constraints require encryption in transit.

## Future Hardening Ideas
- Introduce lightweight authentication for link creation (e.g., API keys per client or OAuth) and back it with ingress-side rate limiting using NGINX annotations to enforce quotas before traffic reaches the services.
- Introduce RBAC-bound service accounts per microservice to limit Kubernetes API access.
- Add PodSecurityStandards (baseline or restricted) and admission controllers to enforce non-root execution.
- Instrument logging and metrics collection (Prometheus/Grafana, OpenTelemetry) to support security monitoring.
- Automate container image vulnerability scanning in CI (e.g., Trivy, Snyk).
- Back up the Postgres PVC regularly and encrypt volumes when running on cloud storage classes.

Security is an iterative process; this project demonstrates key best practices while leaving headroom for production-grade enhancements.
