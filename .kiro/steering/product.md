# Product

**kiro-api** is a support cases REST API that allows clients to create, retrieve, update, and manage support tickets.

## Purpose

Provides a backend HTTP API for support ticket management. Consumers are expected to be internal tooling or front-end clients that need to interact with support case data.

## Key Domains

- **Support Cases / Tickets**: Core entity — creation, retrieval, update, status transitions
- **Backend Database**: Persistent storage for all ticket data, accessed exclusively through a data access layer

## Architecture Principles

- All public-facing endpoints are documented via FastAPI's auto-generated OpenAPI/Swagger docs
- Business data structures are defined using Pydantic models
- The API layer never accesses the database directly — all data operations go through the data access layer (DAL)
