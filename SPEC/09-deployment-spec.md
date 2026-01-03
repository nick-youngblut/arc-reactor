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
│  │  (production)   │   │  (dev)          │   │  branches       │            │
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
│  │  Production Environment   │   │  Dev Environment          │              │
│  │                           │   │                           │              │
│  │  • arc-reactor (prod)     │   │  • arc-reactor-dev        │              │
│  │  • IAP protected          │   │  • IAP protected          │              │
│  │  • Production secrets     │   │  • Dev secrets            │              │
│  └───────────────────────────┘   └───────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Infrastructure Components

### Cloud Run Service

| Setting | Production | Dev |
|---------|------------|---------|
| Service name | `arc-reactor` | `arc-reactor-dev` |
| Region | `us-west1` | `us-west1` |
| Min instances | 1 | 0 |
| Max instances | 10 | 3 |
| Memory | 2Gi | 1Gi |
| CPU | 2 | 1 |
| Timeout | 3600s | 3600s |
| Concurrency | 80 | 40 |

**Cloud SQL Connection:**
- Attach Cloud SQL instance to Cloud Run service
- Provide `DATABASE_URL` using the Cloud SQL Unix socket for Cloud Run
- For GCP Batch jobs, pass `DATABASE_URL` using the Cloud SQL **Private IP**
  (not the Unix socket), e.g. `postgresql+asyncpg://USER:PASS@PRIVATE_IP:5432/DB`

### GCS Buckets

| Bucket | Purpose | Environment |
|--------|---------|-------------|
| `arc-reactor-runs` | Production run data | Production |
| `arc-reactor-runs-dev` | Dev run data | Dev |
| `arc-reactor-build-cache` | Build artifacts | Shared |

### Cloud SQL (PostgreSQL)

| Instance | Environment |
|----------|-------------|
| `arc-reactor-db` | Production |
| `arc-reactor-db-dev` | Dev |



### Secret Manager

| Secret | Environments |
|--------|--------------|
| `benchling-prod-api-key` | Prod |
| `benchling-prod-database-uri` | Prod |
| `benchling-prod-app-client-id` | Prod |
| `benchling-prod-app-client-secret` | Prod |
| `benchling-test-api-key` | Dev/Test |
| `benchling-test-database-uri` | Dev/Test |
| `benchling-test-app-client-id` | Dev/Test |
| `benchling-test-app-client-secret` | Dev/Test |
| `google-api-key` | Both |

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

**Run status updates (required):**
- The orchestrator image must include `orchestrator/update_status.py` at `/update_status.py`.
- The container needs `asyncpg` and access to Cloud SQL via `DATABASE_URL`.
- Batch job spec must pass `DATABASE_URL` and `RUN_ID` to the container.
- `DATABASE_URL` for Batch must use the Cloud SQL **Private IP**, not the Unix socket.

**Nextflow hook invocation (example):**
```groovy
workflow.onStart {
  "python3 /update_status.py ${params.run_id} running --started_at '${new Date().toInstant().toString()}'".execute()
}
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
  PROJECT_ID: arc-genomics02
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
            echo "service=arc-reactor" >> $GITHUB_OUTPUT
          else
            echo "env=test" >> $GITHUB_OUTPUT
            echo "service=arc-reactor-dev" >> $GITHUB_OUTPUT
          fi
          
      - name: Build and push
        run: |
          DOCKER_BUILDKIT=1 docker build \
            --secret id=GITHUB_TOKEN,env=GITHUB_TOKEN \
            -t us-docker.pkg.dev/$PROJECT_ID/arc-reactor/${{ steps.env.outputs.service }}:${{ github.sha }} \
            -t us-docker.pkg.dev/$PROJECT_ID/arc-reactor/${{ steps.env.outputs.service }}:latest \
            .
          docker push us-docker.pkg.dev/$PROJECT_ID/arc-reactor/${{ steps.env.outputs.service }}:${{ github.sha }}
          docker push us-docker.pkg.dev/$PROJECT_ID/arc-reactor/${{ steps.env.outputs.service }}:latest
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
            echo "service=arc-reactor" >> $GITHUB_OUTPUT
          else
            echo "env=test" >> $GITHUB_OUTPUT
            echo "service=arc-reactor-dev" >> $GITHUB_OUTPUT
          fi
          
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: ${{ steps.env.outputs.service }}
          region: ${{ env.REGION }}
          image: us-docker.pkg.dev/${{ env.PROJECT_ID }}/arc-reactor/${{ steps.env.outputs.service }}:${{ github.sha }}
          flags: |
            --min-instances=1
            --max-instances=10
            --memory=2Gi
            --cpu=2
            --timeout=3600
            --concurrency=80
            --service-account=arc-reactor@${{ env.PROJECT_ID }}.iam.gserviceaccount.com
            --set-env-vars=DYNACONF=${{ steps.env.outputs.env }}
            --set-secrets=BENCHLING_PROD_API_KEY=benchling-prod-api-key:latest
            --set-secrets=BENCHLING_PROD_DATABASE_URI=benchling-prod-database-uri:latest
            --set-secrets=BENCHLING_PROD_APP_CLIENT_ID=benchling-prod-app-client-id:latest
            --set-secrets=BENCHLING_PROD_APP_CLIENT_SECRET=benchling-prod-app-client-secret:latest
            --set-secrets=BENCHLING_TEST_API_KEY=benchling-test-api-key:latest
            --set-secrets=BENCHLING_TEST_DATABASE_URI=benchling-test-database-uri:latest
            --set-secrets=BENCHLING_TEST_APP_CLIENT_ID=benchling-test-app-client-id:latest
            --set-secrets=BENCHLING_TEST_APP_CLIENT_SECRET=benchling-test-app-client-secret:latest
            --set-secrets=GOOGLE_API_KEY=google-api-key:latest
            --vpc-connector=projects/${{ env.PROJECT_ID }}/locations/${{ env.REGION }}/connectors/serverless-connector
            --ingress=internal-and-cloud-load-balancing
```

## Environment Configuration

### Production (`DYNACONF=prod`)

```yaml
# settings.yaml - prod section
prod:
  debug: false
  gcp_project: "arc-genomics02"
  gcp_region: "us-west1"
  nextflow_bucket: "arc-reactor-runs"
  log_level: "INFO"
```

### Dev/Test (`DYNACONF=test`)

```yaml
# settings.yaml - test section
test:
  debug: true
  gcp_project: "multi-omics-dev"
  gcp_region: "us-west1"
  nextflow_bucket: "arc-reactor-runs-dev"
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
        name  = "DYNACONF"
        value = var.environment
      }
      
      env {
        name = "BENCHLING_PROD_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.benchling_prod_api_key.id
            version = "latest"
          }
        }
      }

      env {
        name = "BENCHLING_PROD_DATABASE_URI"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.benchling_prod_database_uri.id
            version = "latest"
          }
        }
      }

      env {
        name = "BENCHLING_PROD_APP_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.benchling_prod_app_client_id.id
            version = "latest"
          }
        }
      }

      env {
        name = "BENCHLING_PROD_APP_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.benchling_prod_app_client_secret.id
            version = "latest"
          }
        }
      }

      env {
        name = "BENCHLING_TEST_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.benchling_test_api_key.id
            version = "latest"
          }
        }
      }

      env {
        name = "BENCHLING_TEST_DATABASE_URI"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.benchling_test_database_uri.id
            version = "latest"
          }
        }
      }

      env {
        name = "BENCHLING_TEST_APP_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.benchling_test_app_client_id.id
            version = "latest"
          }
        }
      }

      env {
        name = "BENCHLING_TEST_APP_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.benchling_test_app_client_secret.id
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
  name             = "arc-reactor-db"
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

# Note: User accounts and preferences are stored in Cloud SQL (users table)
# rather than Firestore to consolidate all application state in a single database.
```

## Deployment Procedures

### Standard Deployment

1. **Create PR** → Runs tests automatically
2. **Merge to develop** → Deploys to dev
3. **Test in dev** → Manual verification
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
gcloud run revisions list --service=arc-reactor --region=us-west1

# Route traffic to previous revision
gcloud run services update-traffic arc-reactor \
  --region=us-west1 \
  --to-revisions=arc-reactor-00042-abc=100
```

## Monitoring and Alerting

### Health Checks

| Check | Endpoint | Interval |
|-------|----------|----------|
| Liveness | `/health` | 30s |
| Readiness | `/ready` | 30s |

Readiness returns 200 when critical dependencies are healthy, and 503 only when
critical dependencies fail. Non-critical failures (e.g., Benchling or Gemini)
return 200 with a degraded status in the response body.

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
gcloud sql backups restore BACKUP_ID arc-reactor-db \
  --restore-instance=arc-reactor-db
```

**GCS Recovery:**
```bash
# List object versions
gsutil ls -a gs://arc-reactor-runs/runs/RUN_ID/

# Restore specific version
gsutil cp gs://arc-reactor-runs/runs/RUN_ID/file#VERSION gs://arc-reactor-runs/runs/RUN_ID/file
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
| GCP Batch (10 runs/day) | $500 |
| Gemini API (estimated 10M tokens/day) | ~$150 |
| Networking | $50 |
| **Total** | **~$835/month** |

### Cost Optimization

- Cloud Run min instances = 1 (avoid cold starts)
- GCS lifecycle policies for work directories (must retain `work/` long enough to support `-resume` recovery; see `SPEC/12-recovery-spec.md`)
- Spot instances for Batch jobs
- Reserved capacity for predictable workloads
