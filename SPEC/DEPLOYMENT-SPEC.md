# Arc Reactor - Deployment Specification

## Overview

The platform is deployed on Google Cloud Platform using Cloud Run for the web application and GCP Batch for pipeline execution. Deployment follows GitOps principles with automated CI/CD pipelines.

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            GitHub Repository                                │
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │  main branch    │   │  develop branch │   │  feature/*      │            │
│  │  (production)   │   │  (staging)      │   │  branches       │            │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘            │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions CI/CD                                │
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │  Test           │   │  Build          │   │  Deploy         │            │
│  │  • Lint         │──▶│  • Docker       │──▶│  • Cloud Run    │            │
│  │  • Unit tests   │   │  • Push to GCR  │   │  • IAP config   │            │
│  │  • Type check   │   │                 │   │                 │            │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
            │                     │
            ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Google Cloud Platform                                │
│                                                                             │
│  ┌───────────────────────────┐   ┌───────────────────────────┐              │
│  │  Production Environment   │   │  Staging Environment      │              │
│  │                           │   │                           │              │
│  │  • arc-nf-platform (prod) │   │  • arc-nf-platform-staging│              │
│  │  • IAP protected          │   │  • IAP protected          │              │
│  │  • Production secrets     │   │  • Staging secrets        │              │
│  └───────────────────────────┘   └───────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Infrastructure Components

### Cloud Run Service

| Setting | Production | Staging |
|---------|------------|---------|
| Service name | `arc-nf-platform` | `arc-nf-platform-staging` |
| Region | `us-west1` | `us-west1` |
| Min instances | 1 | 0 |
| Max instances | 10 | 3 |
| Memory | 2Gi | 1Gi |
| CPU | 2 | 1 |
| Timeout | 3600s | 3600s |
| Concurrency | 80 | 40 |

**Cloud SQL Connection:**
- Attach Cloud SQL instance to Cloud Run service
- Provide `DATABASE_URL` using the Cloud SQL Unix socket

### GCS Buckets

| Bucket | Purpose | Environment |
|--------|---------|-------------|
| `arc-nf-pipeline-runs` | Production run data | Production |
| `arc-nf-pipeline-runs-staging` | Staging run data | Staging |
| `arc-nf-platform-build-cache` | Build artifacts | Shared |

### Cloud SQL (PostgreSQL)

| Instance | Environment |
|----------|-------------|
| `arc-nf-platform-db` | Production |
| `arc-nf-platform-db-staging` | Staging |

### Firestore (User Accounts)

| Database | Environment |
|----------|-------------|
| `(default)` | Production |
| `staging` | Staging |

### Secret Manager

| Secret | Environments |
|--------|--------------|
| `benchling-warehouse-password` | Both |
| `anthropic-api-key-prod` | Production |
| `anthropic-api-key-staging` | Staging |

## Container Build

### Dockerfile

```dockerfile
# Multi-stage build for FastAPI + Next.js static

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund

# Build static export
COPY frontend ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/pyproject.toml backend/
RUN --mount=type=secret,id=GITHUB_TOKEN \
    GITHUB_TOKEN=$(cat /run/secrets/GITHUB_TOKEN) \
    pip install --no-cache-dir -e ./backend

# Copy application code
COPY backend /app/backend

# Copy built frontend
COPY --from=frontend-build /app/frontend/out /app/frontend/out

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    FRONTEND_OUT_DIR=/app/frontend/out

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Nextflow Orchestrator Container

```dockerfile
# Dockerfile.orchestrator
FROM nextflow/nextflow:24.04.4

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH="/root/google-cloud-sdk/bin:$PATH"

# Install PostgreSQL client
RUN pip3 install --no-cache-dir asyncpg

# Copy scripts
COPY orchestrator/entrypoint.sh /entrypoint.sh
COPY orchestrator/update_status.py /update_status.py
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PROJECT_ID: arc-ctc-project
  REGION: us-west1
  
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -e ./backend[dev]
          
      - name: Lint
        run: |
          ruff check backend/
          mypy backend/
          
      - name: Test
        run: |
          pytest backend/tests/ -v --cov=backend
          
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Frontend lint and type check
        run: |
          cd frontend
          npm ci
          npm run lint
          npm run type-check

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
          
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
        
      - name: Configure Docker
        run: gcloud auth configure-docker
        
      - name: Determine environment
        id: env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "env=prod" >> $GITHUB_OUTPUT
            echo "service=arc-nf-platform" >> $GITHUB_OUTPUT
          else
            echo "env=staging" >> $GITHUB_OUTPUT
            echo "service=arc-nf-platform-staging" >> $GITHUB_OUTPUT
          fi
          
      - name: Build and push
        run: |
          DOCKER_BUILDKIT=1 docker build \
            --secret id=GITHUB_TOKEN,env=GITHUB_TOKEN \
            -t gcr.io/$PROJECT_ID/${{ steps.env.outputs.service }}:${{ github.sha }} \
            -t gcr.io/$PROJECT_ID/${{ steps.env.outputs.service }}:latest \
            .
          docker push gcr.io/$PROJECT_ID/${{ steps.env.outputs.service }}:${{ github.sha }}
          docker push gcr.io/$PROJECT_ID/${{ steps.env.outputs.service }}:latest
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
          
      - name: Determine environment
        id: env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "env=prod" >> $GITHUB_OUTPUT
            echo "service=arc-nf-platform" >> $GITHUB_OUTPUT
          else
            echo "env=staging" >> $GITHUB_OUTPUT
            echo "service=arc-nf-platform-staging" >> $GITHUB_OUTPUT
          fi
          
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: ${{ steps.env.outputs.service }}
          region: ${{ env.REGION }}
          image: gcr.io/${{ env.PROJECT_ID }}/${{ steps.env.outputs.service }}:${{ github.sha }}
          flags: |
            --min-instances=1
            --max-instances=10
            --memory=2Gi
            --cpu=2
            --timeout=3600
            --concurrency=80
            --service-account=arc-nf-platform@${{ env.PROJECT_ID }}.iam.gserviceaccount.com
            --set-env-vars=ENV_FOR_DYNACONF=${{ steps.env.outputs.env }}
            --set-secrets=BENCHLING_WAREHOUSE_PASSWORD=benchling-warehouse-password:latest
            --set-secrets=ANTHROPIC_API_KEY=anthropic-api-key-${{ steps.env.outputs.env }}:latest
            --vpc-connector=projects/${{ env.PROJECT_ID }}/locations/${{ env.REGION }}/connectors/serverless-connector
            --ingress=internal-and-cloud-load-balancing
```

## Environment Configuration

### Production (`ENV_FOR_DYNACONF=prod`)

```yaml
# settings.yaml - production section
production:
  debug: false
  gcp_project: "arc-ctc-project"
  gcp_region: "us-west1"
  nextflow_bucket: "arc-nf-pipeline-runs"
  firestore_database: "(default)"
  log_level: "INFO"
```

### Staging (`ENV_FOR_DYNACONF=staging`)

```yaml
# settings.yaml - staging section
staging:
  debug: true
  gcp_project: "arc-ctc-project"
  gcp_region: "us-west1"
  nextflow_bucket: "arc-nf-pipeline-runs-staging"
  firestore_database: "staging"
  log_level: "DEBUG"
```

## Infrastructure as Code

### Terraform Resources

```hcl
# terraform/main.tf

# Cloud Run service
resource "google_cloud_run_v2_service" "app" {
  name     = var.service_name
  location = var.region
  
  template {
    containers {
      image = var.image
      
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      
      env {
        name  = "ENV_FOR_DYNACONF"
        value = var.environment
      }
      
      env {
        name = "BENCHLING_WAREHOUSE_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.benchling_password.id
            version = "latest"
          }
        }
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
    
    service_account = google_service_account.app.email
  }
}

# IAP configuration
resource "google_iap_web_backend_service_iam_binding" "binding" {
  web_backend_service = google_compute_backend_service.app.name
  role                = "roles/iap.httpsResourceAccessor"
  members             = ["group:${var.access_group}"]
}

# GCS bucket
resource "google_storage_bucket" "runs" {
  name     = var.runs_bucket
  location = var.region
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age                   = 30
      matches_prefix        = ["runs/*/work/"]
    }
    action {
      type = "Delete"
    }
  }
}

# Cloud SQL (PostgreSQL)
resource "google_sql_database_instance" "main" {
  name             = "arc-nf-platform-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }
}

# Firestore database (user accounts and preferences)
resource "google_firestore_database" "database" {
  name        = var.firestore_database
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}
```

## Deployment Procedures

### Standard Deployment

1. **Create PR** → Runs tests automatically
2. **Merge to develop** → Deploys to staging
3. **Test in staging** → Manual verification
4. **Merge to main** → Deploys to production

### Hotfix Deployment

1. **Create hotfix branch** from main
2. **Fix and test locally**
3. **Create PR to main** → Runs tests
4. **Merge to main** → Deploys to production
5. **Backport to develop**

### Rollback Procedure

```bash
# List recent revisions
gcloud run revisions list --service=arc-nf-platform --region=us-west1

# Route traffic to previous revision
gcloud run services update-traffic arc-nf-platform \
  --region=us-west1 \
  --to-revisions=arc-nf-platform-00042-abc=100
```

## Monitoring and Alerting

### Health Checks

| Check | Endpoint | Interval |
|-------|----------|----------|
| Liveness | `/health` | 30s |
| Readiness | `/ready` | 30s |

### Cloud Monitoring Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| High error rate | > 5% 5xx in 5 min | Critical |
| High latency | p95 > 10s in 5 min | Warning |
| Instance count | > 8 instances | Warning |
| Memory usage | > 80% for 10 min | Warning |

### Log-Based Metrics

```yaml
# Cloud Logging metrics
metrics:
  - name: run_submissions
    filter: 'jsonPayload.action="run.submit"'
    
  - name: run_failures
    filter: 'jsonPayload.action="run.failed"'
    
  - name: auth_failures
    filter: 'jsonPayload.action="auth.failed"'
```

## Disaster Recovery

### Backup Strategy

| Component | Backup Method | Frequency | Retention |
|-----------|---------------|-----------|-----------|
| Cloud SQL (PostgreSQL) | Automated backups | Daily | 7 days |
| GCS (inputs/results) | Versioning | Continuous | 90 days |
| Container images | GCR retention | Continuous | 90 days |

### Recovery Procedures

**Cloud SQL Recovery:**
```bash
# Restore from backup (example)
gcloud sql backups restore BACKUP_ID arc-nf-platform-db \
  --restore-instance=arc-nf-platform-db
```

**GCS Recovery:**
```bash
# List object versions
gsutil ls -a gs://arc-nf-pipeline-runs/runs/RUN_ID/

# Restore specific version
gsutil cp gs://arc-nf-pipeline-runs/runs/RUN_ID/file#VERSION gs://arc-nf-pipeline-runs/runs/RUN_ID/file
```

### RTO/RPO Targets

| Metric | Target |
|--------|--------|
| Recovery Time Objective (RTO) | 1 hour |
| Recovery Point Objective (RPO) | 1 hour |

## Cost Management

### Cost Allocation

| Resource | Estimated Monthly Cost |
|----------|------------------------|
| Cloud Run (2 instances avg) | $100 |
| GCS (500 GB) | $10 |
| Cloud SQL (db-f1-micro) | $25 |
| Firestore (user accounts) | $5 |
| GCP Batch (10 runs/day) | $500 |
| Networking | $50 |
| **Total** | **~$690/month** |

### Cost Optimization

- Cloud Run min instances = 1 (avoid cold starts)
- GCS lifecycle policies for work directories
- Spot instances for Batch jobs
- Reserved capacity for predictable workloads
