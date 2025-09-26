# Architecture

This document outlines the architecture of the `shortyqr` application.

## Components

The application is composed of three main components:

*   **`url-service`**: A Python FastAPI application responsible for creating, storing, and retrieving shortened URLs. It connects to the PostgreSQL database to persist link data.
*   **`qr-service`**: A Python FastAPI application that generates QR codes for given URLs. It is a stateless service that does not connect to the database.
*   **`postgres`**: A PostgreSQL database used to store the shortened URLs and their metadata.
*   **`frontend`**: A React single-page application that provides the user interface for creating shortened links and viewing QR codes.

## Data Flow

1.  The user interacts with the **frontend** to create a new shortened link.
2.  The **frontend** sends a request to the **`url-service`** API (`/api/links`).
3.  The **`url-service`** generates a unique slug, saves the original URL and slug to the **PostgreSQL** database, and returns the shortened link information to the frontend.
4.  When the user requests a QR code, the **frontend** sends a request to the **`qr-service`** (`/api/qr`) with the shortened URL as a parameter.
5.  The **`qr-service`** generates a QR code image and returns it to the frontend.
6.  When a user accesses a shortened URL (`/r/{slug}`), the request hits the **`url-service`**, which looks up the original URL in the database, records the click, and redirects the user.

## Ingress and Routing

*   An **Ingress** resource manages external access to the services.
*   It uses `path-based` routing to direct traffic:
    *   `/` routes to the **frontend** service.
    *   `/api` routes to the **`url-service`**.
    *   `/qr` routes to the **`qr-service`**.
*   The Ingress is configured for the `nginx-ingress-controller`.

## Stateless Scaling

*   Both the `url-service` and `qr-service` are designed to be stateless. They do not store any session data locally, and their Horizontal Pod Autoscalers scale replicas automatically once average CPU utilization crosses 80%.
*   This allows for horizontal scaling. Multiple replicas of each service can run behind a load balancer, and requests can be distributed among them.
*   **Horizontal Pod Autoscalers (HPAs)** are configured for both services to automatically scale the number of replicas based on CPU utilization.

## PVC-backed Database

*   The PostgreSQL database is stateful. Its data must persist even if the database pod is restarted.
*   A **PersistentVolumeClaim (PVC)** is used to request persistent storage for the database.
*   This ensures that the data is stored on a persistent volume outside of the pod's lifecycle.

## Why a Microservice Split?

The application is split into microservices for the following reasons:

*   **Independent Scaling**: The `url-service` and `qr-service` have different resource requirements and traffic patterns. By splitting them, we can scale them independently. For example, if generating QR codes becomes CPU-intensive, we can scale up the `qr-service` without affecting the `url-service`.
*   **Separation of Concerns**: Each service has a single responsibility. The `url-service` handles URL management, while the `qr-service` handles QR code generation. This makes the codebase easier to understand, develop, and maintain.
*   **Resilience**: If the `qr-service` fails, the core functionality of the `url-service` (creating and redirecting links) remains available.
*   **Technology Flexibility**: While both services are currently written in Python, a microservice architecture would allow us to rewrite a service in a different language or framework if needed, without affecting the other services.
