# NOVA Marketplace

NOVA Marketplace is a production-oriented e-commerce MVP with web and mobile clients backed by a Django REST API. It demonstrates a multi-client marketplace architecture, inventory workflows, sandbox payment and shipping integrations, and AI-assisted inventory analysis.

> This repository is an MVP and is not production-ready. Payment and shipping providers are sandbox adapters, and the system still requires production integration, security review, operational monitoring, and deployment hardening.

## Overview

The repository is organized as a monorepo with three applications:

- `backend/` - Django REST Framework API and business logic
- `web/` - Next.js customer and administration experience
- `mobile/` - Expo / React Native mobile client

## Key Features

- Product catalogue, categories, search, carts, orders, and user accounts
- Inventory tracking and stock-management workflows
- Sandbox payment initiation and signed webhook processing architecture
- Shipping workflow represented through a sandbox provider adapter
- JWT-based authentication for web and mobile clients
- AI-assisted inventory analysis with deterministic local rules and optional OpenAI integration
- OpenAPI schema generation through drf-spectacular
- Docker Compose environment for the API, web client, PostgreSQL, and Redis

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Web | Next.js, React, TypeScript |
| Mobile | React Native, Expo, TypeScript |
| Backend | Python, Django, Django REST Framework, SimpleJWT |
| Data | PostgreSQL in Docker, SQLite for lightweight local development |
| API documentation | OpenAPI, Swagger UI, ReDoc |
| Infrastructure | Docker, Docker Compose, Redis |

## Architecture

Both clients consume the same REST API. The Django backend owns authentication, catalogue, inventory, order, payment, and shipping state. Provider-facing payment and shipping modules are intentionally sandbox implementations so that the application can demonstrate integration boundaries without claiming a live commercial deployment.

## Screenshots

| Web | Mobile |
| --- | --- |
| ![NOVA web home page](docs/screenshots/web-home.png) | ![NOVA mobile home screen](docs/screenshots/mobile-home.png) |

## Getting Started

### Docker Compose

1. Copy the example environment files and provide local development values.
2. Start the stack:

```bash
docker compose up --build
```

3. Apply migrations and create an administrator from the backend container as needed.

### Local development

Each application also contains its own dependency manifest. Configure the backend environment first, run Django migrations, then start the backend, web, and mobile development servers separately. Never commit real `.env` files or provider credentials.

## My Role

I designed and implemented the full-stack MVP across the Django API, Next.js web application, Expo mobile application, database model, Docker environment, and provider-integration boundaries.

## Skills Demonstrated

Full-stack architecture, REST API design, cross-platform client development, relational data modelling, JWT authentication, inventory workflows, webhook-oriented integrations, containerized development, and API documentation.

## Project Status and Limitations

- Production-oriented MVP; not a live production service
- Payments and shipping use sandbox integrations only
- Production tax, legal, observability, backup, and deployment processes are not complete
- Mobile push notifications and external provider configuration require environment-specific setup
- The critical-hardening work on `hardening/critical-fixes` is intentionally not described as part of `main` until that branch is reviewed and merged

## License

No open-source license has been declared. All rights are reserved unless a license is added later.
