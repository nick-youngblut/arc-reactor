# Sprint 1: Foundation & Infrastructure Setup

## Overview

This sprint establishes the foundational infrastructure, project scaffolding, CI/CD pipelines, and core service integrations required for development of the Arc Reactor application.

## References

- [01-project-overview.md](../spec/01-project-overview.md) - Project scope and goals
- [02-architecture-overview.md](../spec/02-architecture-overview.md) - System architecture
- [03-backend-spec.md](../spec/03-backend-spec.md) - Backend configuration
- [07-integration-spec.md](../spec/07-integration-spec.md) - Service integrations
- [08-security-spec.md](../spec/08-security-spec.md) - Security requirements
- [09-deployment-spec.md](../spec/09-deployment-spec.md) - Deployment procedures

---

## Phase 1.1: Project Scaffolding & Development Environment

> **Spec References:**
> - [02-architecture-overview.md#deployment-architecture](../spec/02-architecture-overview.md) - Single container architecture
> - [03-backend-spec.md#project-structure](../spec/03-backend-spec.md) - Backend directory layout
> - [04-frontend-spec.md#project-structure](../spec/04-frontend-spec.md) - Frontend directory layout
> - [09-deployment-spec.md#container-build](../spec/09-deployment-spec.md) - Dockerfile specifications

### Repository Structure

- [ ] Create monorepo root with appropriate `.gitignore`
- [ ] Initialize `backend/` directory structure:
  - [ ] Create `backend/__init__.py`
  - [ ] Create `backend/main.py` - Application factory with lifespan management — *See [03-backend-spec.md#application-factory](../spec/03-backend-spec.md)*
  - [ ] Create `backend/config.py` - Dynaconf settings loader — *See [03-backend-spec.md#configuration-management](../spec/03-backend-spec.md)*
  - [ ] Create `backend/settings.yaml` - Environment configuration file — *See [03-backend-spec.md#environment-variables](../spec/03-backend-spec.md)*
  - [ ] Create `backend/dependencies.py` - FastAPI dependency injection
  - [ ] Create `backend/context.py` - Shared context for agents
  - [ ] Create `backend/api/` directory with `__init__.py`
  - [ ] Create `backend/api/routes/` directory with `__init__.py`
  - [ ] Create `backend/models/` directory with `__init__.py`
  - [ ] Create `backend/services/` directory with `__init__.py` — *See [03-backend-spec.md#services](../spec/03-backend-spec.md)*
  - [ ] Create `backend/agents/` directory with `__init__.py` — *See [05-agentic-features-spec.md](../spec/05-agentic-features-spec.md)*
  - [ ] Create `backend/agents/tools/` directory with `__init__.py`
  - [ ] Create `backend/agents/subagents/` directory with `__init__.py`
  - [ ] Create `backend/utils/` directory with `__init__.py`
  - [ ] Create `backend/tests/` directory with `__init__.py` and `conftest.py`
- [ ] Initialize `frontend/` directory structure:
  - [ ] Create `frontend/app/` directory for App Router pages — *See [04-frontend-spec.md#page-structure](../spec/04-frontend-spec.md)*
  - [ ] Create `frontend/components/` directory — *See [04-frontend-spec.md#components](../spec/04-frontend-spec.md)*
  - [ ] Create `frontend/hooks/` directory — *See [04-frontend-spec.md#custom-hooks](../spec/04-frontend-spec.md)*
  - [ ] Create `frontend/lib/` directory
  - [ ] Create `frontend/stores/` directory — *See [04-frontend-spec.md#state-management](../spec/04-frontend-spec.md)*
  - [ ] Create `frontend/types/` directory
  - [ ] Create `frontend/styles/` directory
  - [ ] Create `frontend/public/` directory

### Backend Setup (FastAPI)

> **Spec References:**
> - [03-backend-spec.md#dependencies](../spec/03-backend-spec.md) - Required Python packages
> - [03-backend-spec.md#configuration-management](../spec/03-backend-spec.md) - Dynaconf setup
> - [11-conf-spec.md](../spec/11-conf-spec.md) - Configuration values

- [ ] Create `backend/pyproject.toml` with dependencies:
  - [ ] FastAPI and Uvicorn
  - [ ] Pydantic v2 for validation
  - [ ] Dynaconf for configuration — *See [03-backend-spec.md#configuration-management](../spec/03-backend-spec.md)*
  - [ ] SQLAlchemy with asyncpg — *See [07-integration-spec.md#cloud-sql-postgresql-integration](../spec/07-integration-spec.md)*
  - [ ] google-cloud-batch — *See [07-integration-spec.md#gcp-batch-integration](../spec/07-integration-spec.md)*
  - [ ] google-cloud-storage — *See [07-integration-spec.md#google-cloud-storage-integration](../spec/07-integration-spec.md)*
  - [ ] google-cloud-secret-manager — *See [08-security-spec.md#secret-management](../spec/08-security-spec.md)*
  - [ ] langchain and langchain-google-genai — *See [05-agentic-features-spec.md#agent-configuration](../spec/05-agentic-features-spec.md)*
  - [ ] benchling-py from git
  - [ ] circuitbreaker for resilience — *See [07-integration-spec.md#circuit-breakers](../spec/07-integration-spec.md)*
  - [ ] Dev dependencies: pytest, pytest-asyncio, ruff, mypy, black
- [ ] Configure Dynaconf in `backend/config.py`:
  - [ ] Load settings from `settings.yaml`
  - [ ] Support environment variable overrides — *See [03-backend-spec.md#environment-variables](../spec/03-backend-spec.md)*
  - [ ] Define settings for `default`, `development`, and `production` environments
- [ ] Populate `backend/settings.yaml` with default configuration — *See [11-conf-spec.md](../spec/11-conf-spec.md)*:
  - [ ] `app_name`: "Arc Reactor"
  - [ ] `gcp_project`: GCP project ID
  - [ ] `gcp_region`: "us-west1"
  - [ ] `nextflow_bucket`: Bucket name for runs — *See [06-data-model-spec.md#google-cloud-storage](../spec/06-data-model-spec.md)*
  - [ ] `nextflow_service_account`: Service account email — *See [08-security-spec.md#service-account-permissions](../spec/08-security-spec.md)*
  - [ ] `orchestrator_image`: Container image URI
  - [ ] `benchling_warehouse_host`: Benchling DB host — *See [07-integration-spec.md#benchling-integration](../spec/07-integration-spec.md)*
  - [ ] `benchling_warehouse_db`: Database name
  - [ ] `gemini_model`: "gemini-3-flash-preview" — *See [11-conf-spec.md#ai-model-configuration](../spec/11-conf-spec.md)*
  - [ ] `gemini_thinking_level`: "low" — *See [11-conf-spec.md#thinking-level-options](../spec/11-conf-spec.md)*
  - [ ] `frontend_out_dir`: Path to static frontend build
  - [ ] `cors_allowed_origins`: List of allowed origins — *See [03-backend-spec.md#cors-configuration](../spec/03-backend-spec.md)*
  - [ ] Circuit breaker thresholds for Benchling and Gemini — *See [07-integration-spec.md#circuit-breakers](../spec/07-integration-spec.md)*
- [ ] Implement basic FastAPI application in `backend/main.py`:
  - [ ] Create FastAPI app instance with metadata
  - [ ] Configure CORS middleware with settings — *See [03-backend-spec.md#cors-configuration](../spec/03-backend-spec.md)*
  - [ ] Add lifespan context manager for startup/shutdown
  - [ ] Mount API routers (placeholder)
  - [ ] Configure static file serving for frontend — *See [03-backend-spec.md#frontend-integration](../spec/03-backend-spec.md)*

### Frontend Setup (Next.js)

> **Spec References:**
> - [04-frontend-spec.md#framework](../spec/04-frontend-spec.md) - Next.js 14 with App Router
> - [04-frontend-spec.md#static-export](../spec/04-frontend-spec.md) - Static export configuration
> - [04-frontend-spec.md#styling](../spec/04-frontend-spec.md) - Tailwind CSS and HeroUI

- [ ] Initialize Next.js 14 project with TypeScript in `frontend/`
- [ ] Configure `next.config.js`:
  - [ ] Enable static export (`output: 'export'`) — *See [04-frontend-spec.md#static-export](../spec/04-frontend-spec.md)*
  - [ ] Configure base path if needed
  - [ ] Set image optimization settings
- [ ] Install and configure Tailwind CSS — *See [04-frontend-spec.md#styling](../spec/04-frontend-spec.md)*:
  - [ ] Create `tailwind.config.js` with Arc brand colors
  - [ ] Configure content paths for purging
  - [ ] Add Tailwind plugins: `@tailwindcss/forms`, `@tailwindcss/typography`
  - [ ] Create `globals.css` with Tailwind directives and base styles
- [ ] Install HeroUI component library — *See [04-frontend-spec.md#styling](../spec/04-frontend-spec.md)*
- [ ] Install additional dependencies:
  - [ ] `@tanstack/react-query` for server state — *See [04-frontend-spec.md#state-management](../spec/04-frontend-spec.md)*
  - [ ] `zustand` for client state — *See [04-frontend-spec.md#state-management](../spec/04-frontend-spec.md)*
  - [ ] `axios` for HTTP requests — *See [04-frontend-spec.md#api-client](../spec/04-frontend-spec.md)*
  - [ ] `ai` (Vercel AI SDK) for chat interface — *See [04-frontend-spec.md#useagentchat-hook](../spec/04-frontend-spec.md)*
  - [ ] `handsontable` and `@handsontable/react` for spreadsheet — *See [04-frontend-spec.md#samplesheeteditor](../spec/04-frontend-spec.md)*
  - [ ] `@monaco-editor/react` for code editor — *See [04-frontend-spec.md#configeditor](../spec/04-frontend-spec.md)*
- [ ] Create root layout (`app/layout.tsx`) — *See [04-frontend-spec.md#root-layout](../spec/04-frontend-spec.md)*:
  - [ ] Set up HTML document structure
  - [ ] Add global providers (query client, theme)
  - [ ] Configure metadata (title, description)
- [ ] Create placeholder pages — *See [04-frontend-spec.md#page-structure](../spec/04-frontend-spec.md)*:
  - [ ] `app/page.tsx` - Home/redirect
  - [ ] `app/workspace/page.tsx` - Main workspace
  - [ ] `app/runs/page.tsx` - Run history
  - [ ] `app/runs/[id]/page.tsx` - Run detail
  - [ ] `app/not-found.tsx` - 404 page

### Development Tooling

- [ ] Configure Python linting with Ruff:
  - [ ] Create `ruff.toml` or `pyproject.toml` section
  - [ ] Enable `E`, `F`, `I` rule sets
  - [ ] Set line length to 100
- [ ] Configure Python formatting with Black:
  - [ ] Set line length to 100 in `pyproject.toml`
- [ ] Configure Python type checking with mypy:
  - [ ] Create `mypy.ini` or `pyproject.toml` section
  - [ ] Enable strict mode for new code
- [ ] Configure ESLint for frontend:
  - [ ] Use Next.js recommended config
  - [ ] Add TypeScript rules
  - [ ] Configure import ordering
- [ ] Configure Prettier for frontend:
  - [ ] Create `.prettierrc` with Tailwind plugin
  - [ ] Set consistent quote and semicolon styles
- [ ] Create pre-commit hooks configuration:
  - [ ] Run Ruff and Black on Python files
  - [ ] Run ESLint and Prettier on TypeScript files

### Docker Development Environment

> **Spec References:**
> - [09-deployment-spec.md#dockerfile](../spec/09-deployment-spec.md) - Production Dockerfile
> - [09-deployment-spec.md#container-build](../spec/09-deployment-spec.md) - Multi-stage build

- [ ] Create `Dockerfile` for production build — *See [09-deployment-spec.md#dockerfile](../spec/09-deployment-spec.md)*:
  - [ ] Stage 1: Build frontend with Node.js
  - [ ] Stage 2: Python runtime with backend
  - [ ] Copy built frontend to backend serving directory
  - [ ] Configure health check
  - [ ] Set entrypoint for Uvicorn
- [ ] Create `Dockerfile.dev` for local development:
  - [ ] Support hot reloading for backend
  - [ ] Mount source directories
- [ ] Create `docker-compose.yml` for local development:
  - [ ] Backend service with volume mounts
  - [ ] Frontend service for development
  - [ ] PostgreSQL service for local database
  - [ ] Environment variable configuration
- [ ] Create `.dockerignore` to exclude unnecessary files

### Repository Guidelines

- [ ] Create or update root `GEMINI.md` with repository guidelines:
  - [ ] Project structure documentation
  - [ ] Build and test commands
  - [ ] Coding style conventions
  - [ ] Testing guidelines
  - [ ] Commit message format
- [ ] Create `backend/GEMINI.md` with backend-specific guidelines
- [ ] Create `frontend/GEMINI.md` with frontend-specific guidelines
- [ ] Create `AGENTS.md` if not present
- [ ] Update `.gitignore` for both Python and Node.js artifacts

---

## Phase 1.2: GCP Infrastructure & CI/CD

> **Spec References:**
> - [02-architecture-overview.md#cloud-native-serverless](../spec/02-architecture-overview.md) - Cloud architecture
> - [08-security-spec.md#service-account-permissions](../spec/08-security-spec.md) - IAM configuration
> - [09-deployment-spec.md#infrastructure-components](../spec/09-deployment-spec.md) - GCP resources
> - [09-deployment-spec.md#github-actions-cicd](../spec/09-deployment-spec.md) - CI/CD pipeline

### GCP Project Resources

- [ ] Create or configure GCP project for Arc Reactor
- [ ] Enable required GCP APIs:
  - [ ] Cloud Run API — *See [02-architecture-overview.md#web-application-layer](../spec/02-architecture-overview.md)*
  - [ ] Cloud SQL Admin API — *See [02-architecture-overview.md#data-layer](../spec/02-architecture-overview.md)*
  - [ ] Cloud Storage API — *See [02-architecture-overview.md#data-layer](../spec/02-architecture-overview.md)*
  - [ ] Cloud Batch API — *See [02-architecture-overview.md#compute-layer](../spec/02-architecture-overview.md)*
  - [ ] Secret Manager API — *See [08-security-spec.md#secret-management](../spec/08-security-spec.md)*
  - [ ] Cloud Logging API
  - [ ] Identity-Aware Proxy API — *See [08-security-spec.md#identity-aware-proxy-iap](../spec/08-security-spec.md)*
  - [ ] Artifact Registry API (for container images)

### Service Accounts & IAM

> **Spec References:**
> - [08-security-spec.md#service-account-permissions](../spec/08-security-spec.md) - Complete IAM roles

- [ ] Create Cloud Run service account (`arc-reactor@PROJECT.iam.gserviceaccount.com`) — *See [08-security-spec.md#cloud-run-service-account](../spec/08-security-spec.md)*:
  - [ ] Grant `roles/cloudsql.client`
  - [ ] Grant `roles/storage.objectAdmin` for pipeline bucket
  - [ ] Grant `roles/storage.objectViewer` for NGS data bucket
  - [ ] Grant `roles/batch.jobsEditor`
  - [ ] Grant `roles/logging.logWriter`
  - [ ] Grant `roles/secretmanager.secretAccessor`
- [ ] Create Batch orchestrator service account (`nextflow-orchestrator@PROJECT.iam.gserviceaccount.com`) — *See [08-security-spec.md#batch-orchestrator-service-account](../spec/08-security-spec.md)*:
  - [ ] Grant `roles/cloudsql.client`
  - [ ] Grant `roles/storage.objectAdmin` for pipeline bucket
  - [ ] Grant `roles/storage.objectViewer` for NGS data bucket
  - [ ] Grant `roles/batch.jobsEditor`
  - [ ] Grant `roles/logging.logWriter`
- [ ] Create Nextflow tasks service account (`nextflow-tasks@PROJECT.iam.gserviceaccount.com`) — *See [08-security-spec.md#nextflow-tasks-service-account](../spec/08-security-spec.md)*:
  - [ ] Grant `roles/storage.objectAdmin` for work directory
  - [ ] Grant `roles/storage.objectViewer` for NGS data bucket
  - [ ] Grant `roles/logging.logWriter`

### Cloud SQL (PostgreSQL)

> **Spec References:**
> - [06-data-model-spec.md#cloud-sql-postgresql](../spec/06-data-model-spec.md) - Database schema
> - [07-integration-spec.md#cloud-sql-postgresql-integration](../spec/07-integration-spec.md) - Connection configuration
> - [09-deployment-spec.md#cloud-sql-postgresql](../spec/09-deployment-spec.md) - Instance settings

- [ ] Create Cloud SQL PostgreSQL instance for dev environment:
  - [ ] Instance name: `arc-reactor-db-dev`
  - [ ] PostgreSQL version: 15
  - [ ] Region: `us-west1`
  - [ ] Machine type: `db-f1-micro` for dev
  - [ ] Enable private IP — *See [07-integration-spec.md#connection-configuration](../spec/07-integration-spec.md)*
  - [ ] Configure automated backups — *See [06-data-model-spec.md#backup-and-recovery](../spec/06-data-model-spec.md)*
- [ ] Create Cloud SQL PostgreSQL instance for prod environment:
  - [ ] Instance name: `arc-reactor-db`
  - [ ] Same configuration as dev but larger machine type
- [ ] Create database user with appropriate permissions
- [ ] Create databases: `arc_reactor_dev`, `arc_reactor_prod`

### GCS Buckets

> **Spec References:**
> - [06-data-model-spec.md#google-cloud-storage](../spec/06-data-model-spec.md) - Bucket structure and lifecycle
> - [07-integration-spec.md#google-cloud-storage-integration](../spec/07-integration-spec.md) - GCS operations

- [ ] Create dev runs bucket (`arc-reactor-runs-dev`) — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*:
  - [ ] Region: `us-west1`
  - [ ] Uniform bucket-level access enabled
  - [ ] Configure lifecycle policy for `runs/*/work/` (30-day deletion) — *See [06-data-model-spec.md#file-lifecycle](../spec/06-data-model-spec.md)*
  - [ ] Enable versioning for `inputs/` and `results/` paths
  - [ ] Configure soft delete with 7-day recovery — *See [06-data-model-spec.md#backup-and-recovery](../spec/06-data-model-spec.md)*
- [ ] Create prod runs bucket (`arc-reactor-runs`):
  - [ ] Same configuration as dev bucket
- [ ] Configure IAM bindings for service accounts

### Secret Manager

> **Spec References:**
> - [08-security-spec.md#secret-management](../spec/08-security-spec.md) - Secret storage

- [ ] Create secret for Benchling warehouse password:
  - [ ] Secret name: `benchling-warehouse-password`
  - [ ] Add secret version with actual password
- [ ] Create secret for Google API key — *See [11-conf-spec.md#environment-variables](../spec/11-conf-spec.md)*:
  - [ ] Secret name: `google-api-key`
  - [ ] Add secret version with Gemini API key
- [ ] Grant secret accessor role to Cloud Run service account

### VPC & Networking

> **Spec References:**
> - [08-security-spec.md#network-security](../spec/08-security-spec.md) - VPC configuration
> - [08-security-spec.md#egress-controls](../spec/08-security-spec.md) - Allowed destinations

- [ ] Create or configure VPC network for Arc Reactor
- [ ] Create Serverless VPC Connector for Cloud Run:
  - [ ] Region: `us-west1`
  - [ ] Configure IP range
- [ ] Configure Cloud NAT for egress traffic
- [ ] Configure firewall rules — *See [08-security-spec.md#firewall-rules](../spec/08-security-spec.md)*:
  - [ ] Allow IAP ranges to Cloud Run
  - [ ] Allow internal VPC traffic
  - [ ] Default deny all other ingress

### IAP Configuration

> **Spec References:**
> - [07-integration-spec.md#gcp-iap-integration](../spec/07-integration-spec.md) - IAP authentication flow
> - [08-security-spec.md#identity-aware-proxy-iap](../spec/08-security-spec.md) - IAP settings

- [ ] Configure Cloud Run backend service for IAP:
  - [ ] Enable IAP on the backend service
  - [ ] Configure OAuth consent screen
- [ ] Create IAP access policy — *See [08-security-spec.md#authorized-groups](../spec/08-security-spec.md)*:
  - [ ] Create Google Group for users (`arc-reactor-users@arcinstitute.org`)
  - [ ] Create Google Group for admins (`arc-reactor-admins@arcinstitute.org`)
  - [ ] Grant `roles/iap.httpsResourceAccessor` to user group

### GitHub Actions CI/CD

> **Spec References:**
> - [09-deployment-spec.md#github-actions-workflow](../spec/09-deployment-spec.md) - Complete workflow YAML

- [ ] Create `.github/workflows/ci.yml` for pull request checks:
  - [ ] Checkout code
  - [ ] Set up Python 3.11
  - [ ] Install backend dependencies
  - [ ] Run Ruff linting
  - [ ] Run mypy type checking
  - [ ] Run pytest
  - [ ] Set up Node.js 20
  - [ ] Install frontend dependencies
  - [ ] Run ESLint
  - [ ] Run TypeScript type checking
  - [ ] Run frontend tests
- [ ] Create `.github/workflows/deploy.yml` for deployment — *See [09-deployment-spec.md#github-actions-workflow](../spec/09-deployment-spec.md)*:
  - [ ] Trigger on push to `main` and `develop` branches
  - [ ] Authenticate to GCP using service account key
  - [ ] Determine environment from branch (main=prod, develop=dev)
  - [ ] Build Docker image with BuildKit
  - [ ] Push to Artifact Registry or GCR
  - [ ] Deploy to Cloud Run with appropriate configuration
  - [ ] Configure environment variables and secrets
- [ ] Add GitHub repository secrets:
  - [ ] `GCP_SA_KEY`: Service account JSON key
  - [ ] `GITHUB_TOKEN`: For private dependencies

### Terraform Infrastructure as Code

> **Spec References:**
> - [09-deployment-spec.md#terraform-resources](../spec/09-deployment-spec.md) - Terraform examples

- [ ] Create `terraform/` directory structure:
  - [ ] `terraform/main.tf` - Main resources
  - [ ] `terraform/variables.tf` - Input variables
  - [ ] `terraform/outputs.tf` - Output values
  - [ ] `terraform/environments/dev.tfvars`
  - [ ] `terraform/environments/prod.tfvars`
- [ ] Define Terraform resources — *See [09-deployment-spec.md#terraform-resources](../spec/09-deployment-spec.md)*:
  - [ ] Cloud Run service
  - [ ] Cloud SQL instance
  - [ ] GCS buckets
  - [ ] Service accounts with IAM bindings
  - [ ] Secret Manager secrets
  - [ ] VPC connector
  - [ ] IAP configuration
- [ ] Create Terraform backend configuration for state storage
- [ ] Document Terraform usage in README

---

## Phase 1.3: Core Service Integrations

> **Spec References:**
> - [07-integration-spec.md](../spec/07-integration-spec.md) - All external integrations
> - [03-backend-spec.md#services](../spec/03-backend-spec.md) - Service layer design

### Benchling Data Warehouse Connection

> **Spec References:**
> - [07-integration-spec.md#benchling-integration](../spec/07-integration-spec.md) - Connection details
> - [07-integration-spec.md#connection-pool](../spec/07-integration-spec.md) - Pool configuration
> - [06-data-model-spec.md#benchling-data-warehouse](../spec/06-data-model-spec.md) - Available tables

- [ ] Create `backend/services/benchling.py` — *See [03-backend-spec.md#benchlingservice](../spec/03-backend-spec.md)*:
  - [ ] Implement `BenchlingService` class
  - [ ] Initialize connection pool with async SQLAlchemy — *See [07-integration-spec.md#connection-pool](../spec/07-integration-spec.md)*
  - [ ] Configure connection parameters from settings
  - [ ] Set pool size to 5 connections
  - [ ] Set max overflow to 10
  - [ ] Set pool timeout to 30 seconds
  - [ ] Set pool recycle to 1800 seconds (30 minutes)
  - [ ] Require SSL mode
- [ ] Implement basic query method:
  - [ ] Accept SQL query and parameters
  - [ ] Return results as DataFrame or dict
  - [ ] Handle connection errors gracefully — *See [07-integration-spec.md#error-handling](../spec/07-integration-spec.md)*
- [ ] Implement connection health check method
- [ ] Add unit tests for Benchling service with mocked database

### Cloud SQL (PostgreSQL) Connection

> **Spec References:**
> - [07-integration-spec.md#cloud-sql-postgresql-integration](../spec/07-integration-spec.md) - Connection configuration

- [ ] Create `backend/services/database.py`:
  - [ ] Configure async SQLAlchemy engine
  - [ ] Support Cloud Run Unix socket connection — *See [07-integration-spec.md#cloud-run-unix-socket](../spec/07-integration-spec.md)*
  - [ ] Support local development with standard connection
  - [ ] Set appropriate pool configuration — *See [07-integration-spec.md#connection-pool](../spec/07-integration-spec.md)*
- [ ] Create async session factory
- [ ] Implement database health check method
- [ ] Create dependency for injecting database session
- [ ] Add to application lifespan (connect on startup, disconnect on shutdown)

### GCS Storage Service

> **Spec References:**
> - [07-integration-spec.md#google-cloud-storage-integration](../spec/07-integration-spec.md) - GCS operations
> - [03-backend-spec.md#storageservice](../spec/03-backend-spec.md) - Service interface
> - [06-data-model-spec.md#object-metadata](../spec/06-data-model-spec.md) - File metadata

- [ ] Create `backend/services/storage.py` — *See [03-backend-spec.md#storageservice](../spec/03-backend-spec.md)*:
  - [ ] Implement `StorageService` class
  - [ ] Initialize Google Cloud Storage client
- [ ] Implement file upload method — *See [07-integration-spec.md#file-upload](../spec/07-integration-spec.md)*:
  - [ ] Accept run ID, filename, and content
  - [ ] Upload to `gs://{bucket}/runs/{run_id}/inputs/{filename}`
  - [ ] Set custom metadata (run-id, user-email, created-at) — *See [06-data-model-spec.md#object-metadata](../spec/06-data-model-spec.md)*
  - [ ] Return GCS URI
- [ ] Implement file download method:
  - [ ] Accept GCS URI or path components
  - [ ] Return file content as string or bytes
- [ ] Implement file listing method:
  - [ ] List files under a given prefix
  - [ ] Return file info (name, size, updated time)
- [ ] Implement file existence check — *See [07-integration-spec.md#file-existence-check](../spec/07-integration-spec.md)*:
  - [ ] Accept list of GCS paths
  - [ ] Return dict mapping path to existence boolean
- [ ] Implement signed URL generation — *See [07-integration-spec.md#signed-url-generation](../spec/07-integration-spec.md)*:
  - [ ] Generate V4 signed URLs for download
  - [ ] Configurable expiration (default 60 minutes)
- [ ] Implement storage health check
- [ ] Add unit tests for storage service

### Google Gemini API Integration

> **Spec References:**
> - [07-integration-spec.md#google-gemini-api-integration](../spec/07-integration-spec.md) - API configuration
> - [11-conf-spec.md#ai-model-configuration](../spec/11-conf-spec.md) - Model parameters
> - [05-agentic-features-spec.md#agent-configuration](../spec/05-agentic-features-spec.md) - LangChain setup

- [ ] Create `backend/services/gemini.py`:
  - [ ] Configure LangChain with init_chat_model — *See [07-integration-spec.md#langchain-integration](../spec/07-integration-spec.md)*
  - [ ] Use `google_genai:gemini-3-flash-preview` model — *See [11-conf-spec.md#ai-model-configuration](../spec/11-conf-spec.md)*
  - [ ] Set temperature to 1.0 (required for thinking)
  - [ ] Set thinking_level from settings — *See [11-conf-spec.md#thinking-level-options](../spec/11-conf-spec.md)*
  - [ ] Support both API key and Vertex AI authentication — *See [07-integration-spec.md#authentication](../spec/07-integration-spec.md)*
- [ ] Implement model initialization function
- [ ] Implement streaming response method — *See [07-integration-spec.md#streaming](../spec/07-integration-spec.md)*
- [ ] Implement Gemini health check (simple completion test)
- [ ] Add error handling for rate limits and API errors — *See [07-integration-spec.md#error-handling](../spec/07-integration-spec.md)*

### Circuit Breakers

> **Spec References:**
> - [07-integration-spec.md#circuit-breakers](../spec/07-integration-spec.md) - Circuit breaker configuration

- [ ] Create `backend/utils/circuit_breaker.py`:
  - [ ] Import circuitbreaker library
  - [ ] Create circuit breaker decorator for Benchling — *See [07-integration-spec.md#circuit-breakers](../spec/07-integration-spec.md)*:
    - [ ] Failure threshold: 5
    - [ ] Recovery timeout: 30 seconds
  - [ ] Create circuit breaker decorator for Gemini:
    - [ ] Failure threshold: 3
    - [ ] Recovery timeout: 60 seconds
- [ ] Apply circuit breakers to service methods:
  - [ ] Wrap Benchling query methods
  - [ ] Wrap Gemini API calls
- [ ] Expose circuit breaker state for readiness checks

### Health Check Endpoints

> **Spec References:**
> - [03-backend-spec.md#health-endpoints](../spec/03-backend-spec.md) - Endpoint specifications
> - [07-integration-spec.md#integration-health-checks](../spec/07-integration-spec.md) - Health check implementation

- [ ] Create `backend/api/routes/health.py` — *See [03-backend-spec.md#health-endpoints](../spec/03-backend-spec.md)*:
  - [ ] Implement `GET /health` endpoint:
    - [ ] Return basic health status
    - [ ] Include service name and version
  - [ ] Implement `GET /ready` endpoint — *See [07-integration-spec.md#readiness-check](../spec/07-integration-spec.md)*:
    - [ ] Check Benchling connection (non-critical)
    - [ ] Check PostgreSQL connection (critical)
    - [ ] Check GCS connection (critical)
    - [ ] Check Batch API access (critical)
    - [ ] Check Gemini API (non-critical)
    - [ ] Return 200 if all critical checks pass
    - [ ] Return 503 if any critical check fails
    - [ ] Include degraded status if non-critical checks fail
    - [ ] Return detailed check results in response body
- [ ] Register health routes in main application
- [ ] Add tests for health check endpoints

### Application Lifespan Management

- [ ] Update `backend/main.py` lifespan context manager:
  - [ ] Initialize Benchling service on startup
  - [ ] Initialize database engine and session factory on startup
  - [ ] Initialize Storage service on startup
  - [ ] Initialize Gemini client on startup
  - [ ] Handle graceful shutdown of connections
  - [ ] Log startup and shutdown events
- [ ] Create FastAPI dependencies for injecting services:
  - [ ] `get_benchling_service()`
  - [ ] `get_db_session()`
  - [ ] `get_storage_service()`
  - [ ] `get_gemini_client()`

### Verification & Smoke Tests

- [ ] Create smoke test script for verifying deployments:
  - [ ] Check health endpoint
  - [ ] Check readiness endpoint
  - [ ] Verify all service connections
- [ ] Add basic integration tests:
  - [ ] Test Benchling connection with simple query
  - [ ] Test PostgreSQL connection with simple query
  - [ ] Test GCS with file upload/download
  - [ ] Test Gemini with simple completion
- [ ] Document local development setup:
  - [ ] Environment variable requirements
  - [ ] Docker compose usage
  - [ ] Service mocking for offline development

---

## Key Deliverables Checklist

- [ ] Deployable skeleton application on Cloud Run (dev environment)
- [ ] FastAPI backend with Dynaconf configuration
- [ ] Next.js frontend with static export configured
- [ ] Working CI/CD pipeline (lint, test, build, deploy)
- [ ] Cloud SQL PostgreSQL instances (dev and prod)
- [ ] GCS buckets with lifecycle policies
- [ ] Service accounts with minimal permissions
- [ ] IAP authentication enabled
- [ ] Benchling data warehouse connection verified
- [ ] GCS storage operations working
- [ ] Gemini API integration working
- [ ] Health and readiness endpoints operational
- [ ] Circuit breakers configured for external services
- [ ] Terraform IaC for infrastructure management
- [ ] Repository documentation (GEMINI.md, README)
