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

- [x] Create monorepo root with appropriate `.gitignore`
- [x] Initialize `backend/` directory structure:
  - [x] Create `backend/__init__.py`
  - [x] Create `backend/main.py` - Application factory with lifespan management — *See [03-backend-spec.md#application-factory](../spec/03-backend-spec.md)*
  - [x] Create `backend/config.py` - Dynaconf settings loader — *See [03-backend-spec.md#configuration-management](../spec/03-backend-spec.md)*
  - [x] Create `backend/settings.yaml` - Environment configuration file — *See [03-backend-spec.md#environment-variables](../spec/03-backend-spec.md)*
  - [x] Create `backend/dependencies.py` - FastAPI dependency injection
  - [x] Create `backend/context.py` - Shared context for agents
  - [x] Create `backend/api/` directory with `__init__.py`
  - [x] Create `backend/api/routes/` directory with `__init__.py`
  - [x] Create `backend/models/` directory with `__init__.py`
  - [x] Create `backend/services/` directory with `__init__.py` — *See [03-backend-spec.md#services](../spec/03-backend-spec.md)*
  - [x] Create `backend/agents/` directory with `__init__.py` — *See [05-agentic-features-spec.md](../spec/05-agentic-features-spec.md)*
  - [x] Create `backend/agents/tools/` directory with `__init__.py`
  - [x] Create `backend/agents/subagents/` directory with `__init__.py`
  - [x] Create `backend/utils/` directory with `__init__.py`
  - [x] Create `backend/tests/` directory with `__init__.py` and `conftest.py`
- [x] Initialize `frontend/` directory structure:
  - [x] Create `frontend/app/` directory for App Router pages — *See [04-frontend-spec.md#page-structure](../spec/04-frontend-spec.md)*
  - [x] Create `frontend/components/` directory — *See [04-frontend-spec.md#components](../spec/04-frontend-spec.md)*
  - [x] Create `frontend/hooks/` directory — *See [04-frontend-spec.md#custom-hooks](../spec/04-frontend-spec.md)*
  - [x] Create `frontend/lib/` directory
  - [x] Create `frontend/stores/` directory — *See [04-frontend-spec.md#state-management](../spec/04-frontend-spec.md)*
  - [x] Create `frontend/types/` directory
  - [x] Create `frontend/styles/` directory
  - [x] Create `frontend/public/` directory

### Backend Setup (FastAPI)

> **Spec References:**
> - [03-backend-spec.md#dependencies](../spec/03-backend-spec.md) - Required Python packages
> - [03-backend-spec.md#configuration-management](../spec/03-backend-spec.md) - Dynaconf setup
> - [11-conf-spec.md](../spec/11-conf-spec.md) - Configuration values

- [x] Create `backend/pyproject.toml` with dependencies:
  - [x] FastAPI and Uvicorn
  - [x] Pydantic v2 for validation
  - [x] Dynaconf for configuration — *See [03-backend-spec.md#configuration-management](../spec/03-backend-spec.md)*
  - [x] SQLAlchemy with asyncpg — *See [07-integration-spec.md#cloud-sql-postgresql-integration](../spec/07-integration-spec.md)*
  - [x] google-cloud-batch — *See [07-integration-spec.md#gcp-batch-integration](../spec/07-integration-spec.md)*
  - [x] google-cloud-storage — *See [07-integration-spec.md#google-cloud-storage-integration](../spec/07-integration-spec.md)*
  - [x] google-cloud-secret-manager — *See [08-security-spec.md#secret-management](../spec/08-security-spec.md)*
  - [x] langchain and langchain-google-genai — *See [05-agentic-features-spec.md#agent-configuration](../spec/05-agentic-features-spec.md)*
  - [x] benchling-py from git
  - [x] circuitbreaker for resilience — *See [07-integration-spec.md#circuit-breakers](../spec/07-integration-spec.md)*
  - [x] Dev dependencies: pytest, pytest-asyncio, ruff, mypy, black
- [x] Configure Dynaconf in `backend/config.py`:
  - [x] Load settings from `settings.yaml`
  - [x] Support environment variable overrides — *See [03-backend-spec.md#environment-variables](../spec/03-backend-spec.md)*
  - [x] Define settings for `default`, `development`, and `production` environments
- [x] Populate `backend/settings.yaml` with default configuration — *See [11-conf-spec.md](../spec/11-conf-spec.md)*:
  - [x] `app_name`: "Arc Reactor"
  - [x] `gcp_project`: GCP project ID
  - [x] `gcp_region`: "us-west1"
  - [x] `nextflow_bucket`: Bucket name for runs — *See [06-data-model-spec.md#google-cloud-storage](../spec/06-data-model-spec.md)*
  - [x] `nextflow_service_account`: Service account email — *See [08-security-spec.md#service-account-permissions](../spec/08-security-spec.md)*
  - [x] `orchestrator_image`: Container image URI
  - [x] Benchling Dynaconf environment (`DYNACONF`) — *See [07-integration-spec.md#benchling-integration](../spec/07-integration-spec.md)*
  - [x] Benchling credentials via `BENCHLING_{TEST,PROD}_*` env vars
  - [x] `gemini_model`: "gemini-3-flash-preview" — *See [11-conf-spec.md#ai-model-configuration](../spec/11-conf-spec.md)*
  - [x] `gemini_thinking_level`: "low" — *See [11-conf-spec.md#thinking-level-options](../spec/11-conf-spec.md)*
  - [x] `frontend_out_dir`: Path to static frontend build
  - [x] `cors_allowed_origins`: List of allowed origins — *See [03-backend-spec.md#cors-configuration](../spec/03-backend-spec.md)*
  - [x] Circuit breaker thresholds for Benchling and Gemini — *See [07-integration-spec.md#circuit-breakers](../spec/07-integration-spec.md)*
- [x] Implement basic FastAPI application in `backend/main.py`:
  - [x] Create FastAPI app instance with metadata
  - [x] Configure CORS middleware with settings — *See [03-backend-spec.md#cors-configuration](../spec/03-backend-spec.md)*
  - [x] Add lifespan context manager for startup/shutdown
  - [x] Mount API routers (placeholder)
  - [x] Configure static file serving for frontend — *See [03-backend-spec.md#frontend-integration](../spec/03-backend-spec.md)*

### Frontend Setup (Next.js)

> **Spec References:**
> - [04-frontend-spec.md#framework](../spec/04-frontend-spec.md) - Next.js 14 with App Router
> - [04-frontend-spec.md#static-export](../spec/04-frontend-spec.md) - Static export configuration
> - [04-frontend-spec.md#styling](../spec/04-frontend-spec.md) - Tailwind CSS

- [x] Initialize Next.js 14 project with TypeScript in `frontend/`
- [x] Configure `next.config.js`:
  - [x] Enable static export (`output: 'export'`) — *See [04-frontend-spec.md#static-export](../spec/04-frontend-spec.md)*
  - [x] Configure base path if needed
  - [x] Set image optimization settings
- [x] Install and configure Tailwind CSS — *See [04-frontend-spec.md#styling](../spec/04-frontend-spec.md)*:
  - [x] Create `tailwind.config.js` with Arc brand colors
  - [x] Configure content paths for purging
  - [x] Add Tailwind plugins: `@tailwindcss/forms`, `@tailwindcss/typography`
  - [x] Create `globals.css` with Tailwind directives and base styles
- [x] Configure Tailwind CSS styling — *See [04-frontend-spec.md#styling](../spec/04-frontend-spec.md)*
- [x] Install additional dependencies:
  - [x] `@tanstack/react-query` for server state — *See [04-frontend-spec.md#state-management](../spec/04-frontend-spec.md)*
  - [x] `zustand` for client state — *See [04-frontend-spec.md#state-management](../spec/04-frontend-spec.md)*
  - [x] `axios` for HTTP requests — *See [04-frontend-spec.md#api-client](../spec/04-frontend-spec.md)*
  - [x] `ai` (Vercel AI SDK) for chat interface — *See [04-frontend-spec.md#useagentchat-hook](../spec/04-frontend-spec.md)*
  - [x] `handsontable` and `@handsontable/react` for spreadsheet — *See [04-frontend-spec.md#samplesheeteditor](../spec/04-frontend-spec.md)*
  - [x] `@monaco-editor/react` for code editor — *See [04-frontend-spec.md#configeditor](../spec/04-frontend-spec.md)*
- [x] Create root layout (`app/layout.tsx`) — *See [04-frontend-spec.md#root-layout](../spec/04-frontend-spec.md)*:
  - [x] Set up HTML document structure
  - [x] Add global providers (query client, theme)
  - [x] Configure metadata (title, description)
- [x] Create placeholder pages — *See [04-frontend-spec.md#page-structure](../spec/04-frontend-spec.md)*:
  - [x] `app/page.tsx` - Home/redirect
  - [x] `app/workspace/page.tsx` - Main workspace
  - [x] `app/runs/page.tsx` - Run history
  - [x] `app/runs/[id]/page.tsx` - Run detail
  - [x] `app/not-found.tsx` - 404 page

### Development Tooling

- [x] Configure Python linting with Ruff:
  - [x] Create `ruff.toml` or `pyproject.toml` section
  - [x] Enable `E`, `F`, `I` rule sets
  - [x] Set line length to 100
- [x] Configure Python formatting with Black:
  - [x] Set line length to 100 in `pyproject.toml`
- [x] Configure Python type checking with mypy:
  - [x] Create `mypy.ini` or `pyproject.toml` section
  - [x] Enable strict mode for new code
- [x] Configure ESLint for frontend:
  - [x] Use Next.js recommended config
  - [x] Add TypeScript rules
  - [x] Configure import ordering
- [x] Configure Prettier for frontend:
  - [x] Create `.prettierrc` with Tailwind plugin
  - [x] Set consistent quote and semicolon styles
- [x] Create pre-commit hooks configuration:
  - [x] Run Ruff and Black on Python files
  - [x] Run ESLint and Prettier on TypeScript files

### Docker Development Environment

> **Spec References:**
> - [09-deployment-spec.md#dockerfile](../spec/09-deployment-spec.md) - Production Dockerfile
> - [09-deployment-spec.md#container-build](../spec/09-deployment-spec.md) - Multi-stage build

- [x] Create `Dockerfile` for production build — *See [09-deployment-spec.md#dockerfile](../spec/09-deployment-spec.md)*:
  - [x] Stage 1: Build frontend with Node.js
  - [x] Stage 2: Python runtime with backend
  - [x] Copy built frontend to backend serving directory
  - [x] Configure health check
  - [x] Set entrypoint for Uvicorn
- [x] Create `Dockerfile.dev` for local development:
  - [x] Support hot reloading for backend
  - [x] Mount source directories
- [x] Create `docker-compose.yml` for local development:
  - [x] Backend service with volume mounts
  - [x] Frontend service for development
  - [x] PostgreSQL service for local database
  - [x] Environment variable configuration
- [x] Create `.dockerignore` to exclude unnecessary files

### Repository Guidelines

- [x] Create or update root `GEMINI.md` with repository guidelines:
  - [x] Project structure documentation
  - [x] Build and test commands
  - [x] Coding style conventions
  - [x] Testing guidelines
  - [x] Commit message format
- [x] Create `backend/GEMINI.md` with backend-specific guidelines
- [x] Create `frontend/GEMINI.md` with frontend-specific guidelines
- [x] Create `AGENTS.md` if not present
- [x] Update `.gitignore` for both Python and Node.js artifacts

---

## Phase 1.2: GCP Infrastructure & CI/CD

> **Spec References:**
> - [02-architecture-overview.md#cloud-native-serverless](../spec/02-architecture-overview.md) - Cloud architecture
> - [08-security-spec.md#service-account-permissions](../spec/08-security-spec.md) - IAM configuration
> - [09-deployment-spec.md#infrastructure-components](../spec/09-deployment-spec.md) - GCP resources
> - [09-deployment-spec.md#github-actions-cicd](../spec/09-deployment-spec.md) - CI/CD pipeline

### GCP Project Resources

- [x] Create or configure GCP project for Arc Reactor
- [x] Enable required GCP APIs:
  - [x] Cloud Run API — *See [02-architecture-overview.md#web-application-layer](../spec/02-architecture-overview.md)*
  - [x] Cloud SQL Admin API — *See [02-architecture-overview.md#data-layer](../spec/02-architecture-overview.md)*
  - [x] Cloud Storage API — *See [02-architecture-overview.md#data-layer](../spec/02-architecture-overview.md)*
  - [x] Cloud Batch API — *See [02-architecture-overview.md#compute-layer](../spec/02-architecture-overview.md)*
  - [x] Secret Manager API — *See [08-security-spec.md#secret-management](../spec/08-security-spec.md)*
  - [x] Cloud Logging API
  - [x] Identity-Aware Proxy API — *See [08-security-spec.md#identity-aware-proxy-iap](../spec/08-security-spec.md)*
  - [x] Artifact Registry API (for container images)

### Service Accounts & IAM

> **Spec References:**
> - [08-security-spec.md#service-account-permissions](../spec/08-security-spec.md) - Complete IAM roles

- [x] Create Cloud Run service account (`arc-reactor@PROJECT.iam.gserviceaccount.com`) — *See [08-security-spec.md#cloud-run-service-account](../spec/08-security-spec.md)*:
  - [x] Grant `roles/cloudsql.client`
  - [x] Grant `roles/storage.objectAdmin` for pipeline bucket
  - [x] Grant `roles/storage.objectViewer` for NGS data bucket
  - [x] Grant `roles/batch.jobsEditor`
  - [x] Grant `roles/logging.logWriter`
  - [x] Grant `roles/secretmanager.secretAccessor`
- [x] Create Batch orchestrator service account (`nextflow-orchestrator@PROJECT.iam.gserviceaccount.com`) — *See [08-security-spec.md#batch-orchestrator-service-account](../spec/08-security-spec.md)*:
  - [x] Grant `roles/cloudsql.client`
  - [x] Grant `roles/storage.objectAdmin` for pipeline bucket
  - [x] Grant `roles/storage.objectViewer` for NGS data bucket
  - [x] Grant `roles/batch.jobsEditor`
  - [x] Grant `roles/logging.logWriter`
- [x] Create Nextflow tasks service account (`nextflow-tasks@PROJECT.iam.gserviceaccount.com`) — *See [08-security-spec.md#nextflow-tasks-service-account](../spec/08-security-spec.md)*:
  - [x] Grant `roles/storage.objectAdmin` for work directory
  - [x] Grant `roles/storage.objectViewer` for NGS data bucket
  - [x] Grant `roles/logging.logWriter`

### Cloud SQL (PostgreSQL)

> **Spec References:**
> - [06-data-model-spec.md#cloud-sql-postgresql](../spec/06-data-model-spec.md) - Database schema
> - [07-integration-spec.md#cloud-sql-postgresql-integration](../spec/07-integration-spec.md) - Connection configuration
> - [09-deployment-spec.md#cloud-sql-postgresql](../spec/09-deployment-spec.md) - Instance settings

- [x] Create Cloud SQL PostgreSQL instance for dev environment:
  - [x] Instance name: `arc-reactor-db-dev`
  - [x] PostgreSQL version: 15
  - [x] Region: `us-west1`
  - [x] Machine type: `db-f1-micro` for dev
  - [x] Enable private IP — *See [07-integration-spec.md#connection-configuration](../spec/07-integration-spec.md)*
  - [x] Configure automated backups — *See [06-data-model-spec.md#backup-and-recovery](../spec/06-data-model-spec.md)*
- [x] Create Cloud SQL PostgreSQL instance for prod environment:
  - [x] Instance name: `arc-reactor-db`
  - [x] Same configuration as dev but larger machine type
- [x] Create database user with appropriate permissions
- [x] Create databases: `arc_reactor_dev`, `arc_reactor_prod`

### GCS Buckets

> **Spec References:**
> - [06-data-model-spec.md#google-cloud-storage](../spec/06-data-model-spec.md) - Bucket structure and lifecycle
> - [07-integration-spec.md#google-cloud-storage-integration](../spec/07-integration-spec.md) - GCS operations

- [x] Create dev runs bucket (`arc-reactor-runs-dev`) — *See [06-data-model-spec.md#bucket-structure](../spec/06-data-model-spec.md)*:
  - [x] Region: `us-west1`
  - [x] Uniform bucket-level access enabled
  - [x] Configure lifecycle policy for `runs/*/work/` (30-day deletion) — *See [06-data-model-spec.md#file-lifecycle](../spec/06-data-model-spec.md)*
  - [x] Enable versioning for `inputs/` and `results/` paths
  - [x] Configure soft delete with 7-day recovery — *See [06-data-model-spec.md#backup-and-recovery](../spec/06-data-model-spec.md)*
- [x] Create prod runs bucket (`arc-reactor-runs`):
  - [x] Same configuration as dev bucket
- [x] Configure IAM bindings for service accounts

### Secret Manager

> **Spec References:**
> - [08-security-spec.md#secret-management](../spec/08-security-spec.md) - Secret storage

- [x] Create Benchling secrets for prod/test tenants:
  - [x] `benchling-prod-api-key`, `benchling-prod-database-uri`, `benchling-prod-app-client-id`, `benchling-prod-app-client-secret`
  - [x] `benchling-test-api-key`, `benchling-test-database-uri`, `benchling-test-app-client-id`, `benchling-test-app-client-secret`
  - [x] Add secret version with actual password
- [x] Create secret for Google API key — *See [11-conf-spec.md#environment-variables](../spec/11-conf-spec.md)*:
  - [x] Secret name: `google-api-key`
  - [x] Add secret version with Gemini API key
- [x] Grant secret accessor role to Cloud Run service account

### VPC & Networking

> **Spec References:**
> - [08-security-spec.md#network-security](../spec/08-security-spec.md) - VPC configuration
> - [08-security-spec.md#egress-controls](../spec/08-security-spec.md) - Allowed destinations

- [x] Create or configure VPC network for Arc Reactor
- [x] Create Serverless VPC Connector for Cloud Run:
  - [x] Region: `us-west1`
  - [x] Configure IP range
- [x] Configure Cloud NAT for egress traffic
- [x] Configure firewall rules — *See [08-security-spec.md#firewall-rules](../spec/08-security-spec.md)*:
  - [x] Allow IAP ranges to Cloud Run
  - [x] Allow internal VPC traffic
  - [x] Default deny all other ingress

### IAP Configuration

> **Spec References:**
> - [07-integration-spec.md#gcp-iap-integration](../spec/07-integration-spec.md) - IAP authentication flow
> - [08-security-spec.md#identity-aware-proxy-iap](../spec/08-security-spec.md) - IAP settings

- [x] Configure Cloud Run backend service for IAP:
  - [x] Enable IAP on the backend service
  - [x] Configure OAuth consent screen
- [x] Create IAP access policy — *See [08-security-spec.md#authorized-groups](../spec/08-security-spec.md)*:
  - [x] Create Google Group for users (`arc-reactor-users@arcinstitute.org`)
  - [x] Create Google Group for admins (`arc-reactor-admins@arcinstitute.org`)
  - [x] Grant `roles/iap.httpsResourceAccessor` to user group

### GitHub Actions CI/CD

> **Spec References:**
> - [09-deployment-spec.md#github-actions-workflow](../spec/09-deployment-spec.md) - Complete workflow YAML

- [x] Create `.github/workflows/ci.yml` for pull request checks:
  - [x] Checkout code
  - [x] Set up Python 3.11
  - [x] Install backend dependencies
  - [x] Run Ruff linting
  - [x] Run mypy type checking
  - [x] Run pytest
  - [x] Set up Node.js 20
  - [x] Install frontend dependencies
  - [x] Run ESLint
  - [x] Run TypeScript type checking
  - [x] Run frontend tests
- [x] Create `.github/workflows/deploy.yml` for deployment — *See [09-deployment-spec.md#github-actions-workflow](../spec/09-deployment-spec.md)*:
  - [x] Trigger on push to `main` and `develop` branches
  - [x] Authenticate to GCP using service account key
  - [x] Determine environment from branch (main=prod, develop=dev)
  - [x] Build Docker image with BuildKit
  - [x] Push to Artifact Registry or GCR
  - [x] Deploy to Cloud Run with appropriate configuration
  - [x] Configure environment variables and secrets
- [x] Add GitHub repository secrets:
  - [x] `GCP_SA_KEY`: Service account JSON key
  - [x] `GITHUB_TOKEN`: For private dependencies

### Terraform Infrastructure as Code

> **Spec References:**
> - [09-deployment-spec.md#terraform-resources](../spec/09-deployment-spec.md) - Terraform examples

- [x] Create `terraform/` directory structure:
  - [x] `terraform/main.tf` - Main resources
  - [x] `terraform/variables.tf` - Input variables
  - [x] `terraform/outputs.tf` - Output values
  - [x] `terraform/environments/dev.tfvars`
  - [x] `terraform/environments/prod.tfvars`
- [x] Define Terraform resources — *See [09-deployment-spec.md#terraform-resources](../spec/09-deployment-spec.md)*:
  - [x] Cloud Run service
  - [x] Cloud SQL instance
  - [x] GCS buckets
  - [x] Service accounts with IAM bindings
  - [x] Secret Manager secrets
  - [x] VPC connector
  - [x] IAP configuration
- [x] Create Terraform backend configuration for state storage
- [x] Document Terraform usage in README

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

- [x] Create `backend/services/benchling.py` — *See [03-backend-spec.md#benchlingservice](../spec/03-backend-spec.md)*:
  - [x] Implement `BenchlingService` class
  - [x] Initialize connection pool with async SQLAlchemy — *See [07-integration-spec.md#connection-pool](../spec/07-integration-spec.md)*
  - [x] Configure connection parameters from settings
  - [x] Set pool size to 5 connections
  - [x] Set max overflow to 10
  - [x] Set pool timeout to 30 seconds
  - [x] Set pool recycle to 1800 seconds (30 minutes)
  - [x] Require SSL mode
- [x] Implement basic query method:
  - [x] Accept SQL query and parameters
  - [x] Return results as DataFrame or dict
  - [x] Handle connection errors gracefully — *See [07-integration-spec.md#error-handling](../spec/07-integration-spec.md)*
- [x] Implement connection health check method
- [x] Add unit tests for Benchling service with mocked database

### Cloud SQL (PostgreSQL) Connection

> **Spec References:**
> - [07-integration-spec.md#cloud-sql-postgresql-integration](../spec/07-integration-spec.md) - Connection configuration

- [x] Create `backend/services/database.py`:
  - [x] Configure async SQLAlchemy engine
  - [x] Support Cloud Run Unix socket connection — *See [07-integration-spec.md#cloud-run-unix-socket](../spec/07-integration-spec.md)*
  - [x] Support local development with standard connection
  - [x] Set appropriate pool configuration — *See [07-integration-spec.md#connection-pool](../spec/07-integration-spec.md)*
- [x] Create async session factory
- [x] Implement database health check method
- [x] Create dependency for injecting database session
- [x] Add to application lifespan (connect on startup, disconnect on shutdown)

### GCS Storage Service

> **Spec References:**
> - [07-integration-spec.md#google-cloud-storage-integration](../spec/07-integration-spec.md) - GCS operations
> - [03-backend-spec.md#storageservice](../spec/03-backend-spec.md) - Service interface
> - [06-data-model-spec.md#object-metadata](../spec/06-data-model-spec.md) - File metadata

- [x] Create `backend/services/storage.py` — *See [03-backend-spec.md#storageservice](../spec/03-backend-spec.md)*:
  - [x] Implement `StorageService` class
  - [x] Initialize Google Cloud Storage client
- [x] Implement file upload method — *See [07-integration-spec.md#file-upload](../spec/07-integration-spec.md)*:
  - [x] Accept run ID, filename, and content
  - [x] Upload to `gs://{bucket}/runs/{run_id}/inputs/{filename}`
  - [x] Set custom metadata (run-id, user-email, created-at) — *See [06-data-model-spec.md#object-metadata](../spec/06-data-model-spec.md)*
  - [x] Return GCS URI
- [x] Implement file download method:
  - [x] Accept GCS URI or path components
  - [x] Return file content as string or bytes
- [x] Implement file listing method:
  - [x] List files under a given prefix
  - [x] Return file info (name, size, updated time)
- [x] Implement file existence check — *See [07-integration-spec.md#file-existence-check](../spec/07-integration-spec.md)*:
  - [x] Accept list of GCS paths
  - [x] Return dict mapping path to existence boolean
- [x] Implement signed URL generation — *See [07-integration-spec.md#signed-url-generation](../spec/07-integration-spec.md)*:
  - [x] Generate V4 signed URLs for download
  - [x] Configurable expiration (default 60 minutes)
- [x] Implement storage health check
- [x] Add unit tests for storage service

### Google Gemini API Integration

> **Spec References:**
> - [07-integration-spec.md#google-gemini-api-integration](../spec/07-integration-spec.md) - API configuration
> - [11-conf-spec.md#ai-model-configuration](../spec/11-conf-spec.md) - Model parameters
> - [05-agentic-features-spec.md#agent-configuration](../spec/05-agentic-features-spec.md) - LangChain setup

- [x] Create `backend/services/gemini.py`:
  - [x] Configure LangChain with init_chat_model — *See [07-integration-spec.md#langchain-integration](../spec/07-integration-spec.md)*
  - [x] Use `google_genai:gemini-3-flash-preview` model — *See [11-conf-spec.md#ai-model-configuration](../spec/11-conf-spec.md)*
  - [x] Set temperature to 1.0 (required for thinking)
  - [x] Set thinking_level from settings — *See [11-conf-spec.md#thinking-level-options](../spec/11-conf-spec.md)*
  - [x] Use API key authentication for Gemini — *See [07-integration-spec.md#authentication](../spec/07-integration-spec.md)*
- [x] Implement model initialization function
- [x] Implement streaming response method — *See [07-integration-spec.md#streaming](../spec/07-integration-spec.md)*
- [x] Implement Gemini health check (simple completion test)
- [x] Add error handling for rate limits and API errors — *See [07-integration-spec.md#error-handling](../spec/07-integration-spec.md)*

### Circuit Breakers

> **Spec References:**
> - [07-integration-spec.md#circuit-breakers](../spec/07-integration-spec.md) - Circuit breaker configuration

- [x] Create `backend/utils/circuit_breaker.py`:
  - [x] Import circuitbreaker library
  - [x] Create circuit breaker decorator for Benchling — *See [07-integration-spec.md#circuit-breakers](../spec/07-integration-spec.md)*:
    - [x] Failure threshold: 5
    - [x] Recovery timeout: 30 seconds
  - [x] Create circuit breaker decorator for Gemini:
    - [x] Failure threshold: 3
    - [x] Recovery timeout: 60 seconds
- [x] Apply circuit breakers to service methods:
  - [x] Wrap Benchling query methods
  - [x] Wrap Gemini API calls
- [x] Expose circuit breaker state for readiness checks

### Health Check Endpoints

> **Spec References:**
> - [03-backend-spec.md#health-endpoints](../spec/03-backend-spec.md) - Endpoint specifications
> - [07-integration-spec.md#integration-health-checks](../spec/07-integration-spec.md) - Health check implementation

- [x] Create `backend/api/routes/health.py` — *See [03-backend-spec.md#health-endpoints](../spec/03-backend-spec.md)*:
  - [x] Implement `GET /health` endpoint:
    - [x] Return basic health status
    - [x] Include service name and version
  - [x] Implement `GET /ready` endpoint — *See [07-integration-spec.md#readiness-check](../spec/07-integration-spec.md)*:
    - [x] Check Benchling connection (non-critical)
    - [x] Check PostgreSQL connection (critical)
    - [x] Check GCS connection (critical)
    - [x] Check Batch API access (critical)
    - [x] Check Gemini API (non-critical)
    - [x] Return 200 if all critical checks pass
    - [x] Return 503 if any critical check fails
    - [x] Include degraded status if non-critical checks fail
    - [x] Return detailed check results in response body
- [x] Register health routes in main application
- [x] Add tests for health check endpoints

### Application Lifespan Management

- [x] Update `backend/main.py` lifespan context manager:
  - [x] Initialize Benchling service on startup
  - [x] Initialize database engine and session factory on startup
  - [x] Initialize Storage service on startup
  - [x] Initialize Gemini client on startup
  - [x] Handle graceful shutdown of connections
  - [x] Log startup and shutdown events
- [x] Create FastAPI dependencies for injecting services:
  - [x] `get_benchling_service()`
  - [x] `get_db_session()`
  - [x] `get_storage_service()`
  - [x] `get_gemini_client()`

### Verification & Smoke Tests

- [x] Create smoke test script for verifying deployments:
  - [x] Check health endpoint
  - [x] Check readiness endpoint
  - [x] Verify all service connections
- [x] Add basic integration tests:
  - [x] Test Benchling connection with simple query
  - [x] Test PostgreSQL connection with simple query
  - [x] Test GCS with file upload/download
  - [x] Test Gemini with simple completion
- [x] Document local development setup:
  - [x] Environment variable requirements
  - [x] Docker compose usage
  - [x] Service mocking for offline development

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
