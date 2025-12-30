# Arc Reactor - Security Specification

## Overview

Security is implemented at multiple layers: network, authentication, authorization, and data. The platform follows GCP security best practices and Arc Institute policies.

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GOOGLE CLOUD LOAD BALANCER                           │
│                              (HTTPS Only)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      IDENTITY-AWARE PROXY (IAP)                             │
│                                                                             │
│  • Google Workspace authentication                                          │
│  • Group-based access control                                               │
│  • JWT token generation                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLOUD RUN SERVICE                                 │
│                                                                             │
│  • Ingress: internal-and-cloud-load-balancing                               │
│  • No direct internet access                                                │
│  • Service account with minimal permissions                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
            │ Cloud SQL │   │ Firestore│   │    GCS    │   │ GCP Batch │
            │ (VPC SC)  │   │ (VPC SC) │   │ (VPC SC)  │   │           │
            └───────────┘   └───────────┘   └───────────┘   └───────────┘
```

## Authentication

### Identity-Aware Proxy (IAP)

All user access is authenticated through GCP IAP with Google Workspace SSO.

**Configuration:**
| Setting | Value |
|---------|-------|
| Backend service | Cloud Run |
| Access level | Google Group membership |
| Session duration | 1 hour |
| Re-authentication | Required for sensitive operations |

**Authorized Groups:**
- `arc-nf-platform-users@arcinstitute.org` - Standard users
- `arc-nf-platform-admins@arcinstitute.org` - Administrators

### JWT Token Handling

IAP provides a signed JWT in the `X-Goog-IAP-JWT-Assertion` header.

**Token Claims:**
```json
{
  "iss": "https://cloud.google.com/iap",
  "aud": "/projects/PROJECT_NUMBER/apps/PROJECT_ID",
  "email": "user@arcinstitute.org",
  "sub": "accounts.google.com:USER_ID",
  "hd": "arcinstitute.org",
  "exp": 1703001600,
  "iat": 1703000000
}
```

**Validation Steps:**
1. Verify signature using Google's public keys
2. Check `aud` matches expected audience
3. Verify `exp` is in the future
4. Confirm `hd` is `arcinstitute.org`

### Service-to-Service Authentication

Internal services authenticate using GCP service accounts.

| Service | Service Account |
|---------|-----------------|
| Cloud Run | `arc-nf-platform@project.iam.gserviceaccount.com` |
| Batch Orchestrator | `nextflow-orchestrator@project.iam.gserviceaccount.com` |
| Nextflow Tasks | `nextflow-tasks@project.iam.gserviceaccount.com` |

## Authorization

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **User** | Create runs, view own runs, view all run statuses |
| **Admin** | All user permissions + view all run details, cancel any run |

### Resource-Level Access

| Resource | Owner | Others |
|----------|-------|--------|
| Run details | Full access | Status only |
| Run files | Full access | No access |
| Run logs | Full access | No access |

### API Authorization Rules

```python
# Example authorization middleware
async def authorize_run_access(
    run_id: str,
    user: User,
    required_permission: str,
) -> Run:
    """Check user has permission to access run."""
    run = await get_run(run_id)
    
    if run is None:
        raise HTTPException(404, "Run not found")
    
    # Owner has full access
    if run.user_email == user.email:
        return run
    
    # Admins have full access
    if user.is_admin:
        return run
    
    # Others can only view status
    if required_permission == "view_status":
        return run
    
    raise HTTPException(403, "Access denied")
```

## Service Account Permissions

### Cloud Run Service Account

```yaml
# arc-nf-platform@project.iam.gserviceaccount.com
roles:
  - roles/cloudsql.client          # Cloud SQL access
  - roles/datastore.user           # Firestore user accounts
  - roles/storage.objectAdmin      # GCS read/write (pipeline bucket)
  - roles/storage.objectViewer     # GCS read (NGS data bucket)
  - roles/batch.jobsEditor         # Create/manage Batch jobs
  - roles/logging.logWriter        # Write logs
  - roles/secretmanager.secretAccessor  # Access secrets
```

### Batch Orchestrator Service Account

```yaml
# nextflow-orchestrator@project.iam.gserviceaccount.com
roles:
  - roles/cloudsql.client          # Update run status
  - roles/storage.objectAdmin      # GCS read/write (pipeline bucket)
  - roles/storage.objectViewer     # GCS read (NGS data bucket)
  - roles/batch.jobsEditor         # Submit task jobs
  - roles/logging.logWriter        # Write logs
```

### Nextflow Tasks Service Account

```yaml
# nextflow-tasks@project.iam.gserviceaccount.com
roles:
  - roles/storage.objectAdmin      # GCS work directory
  - roles/storage.objectViewer     # GCS read (NGS data bucket)
  - roles/logging.logWriter        # Write logs
```

## Data Security

### Data Classification

| Data Type | Classification | Protection |
|-----------|---------------|------------|
| User email/name | PII | Encrypted at rest |
| Run parameters | Internal | Encrypted at rest |
| Sample metadata | Research data | Encrypted at rest |
| FASTQ files | Research data | Encrypted at rest |
| Pipeline results | Research data | Encrypted at rest |

### Encryption

**At Rest:**
- Cloud SQL: Google-managed encryption (AES-256)
- Firestore: Google-managed encryption (AES-256)
- GCS: Google-managed encryption (AES-256)
- Secret Manager: Google-managed encryption

**In Transit:**
- All external traffic: TLS 1.3
- All internal traffic: TLS 1.2+
- No plaintext HTTP

### Secret Management

All secrets stored in GCP Secret Manager.

| Secret | Usage |
|--------|-------|
| `benchling-warehouse-password` | Database connection |
| `anthropic-api-key` | AI model access |

**Access Pattern:**
```python
from google.cloud import secretmanager

def get_secret(secret_id: str) -> str:
    """Retrieve secret from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")
```

## Network Security

### VPC Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│                        VPC Network                              │
│                                                                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────┐  │
│  │  Cloud Run      │   │  GCP Batch      │   │  Private      │  │
│  │  (Serverless    │   │  (Compute VMs)  │   │  Google       │  │
│  │   VPC Connector)│   │                 │   │  Access       │  │
│  └────────┬────────┘   └────────┬────────┘   └───────┬───────┘  │
│           │                     │                    │          │
│           └─────────────────────┴────────────────────┘          │
│                                 │                               │
│                         ┌───────▼───────┐                       │
│                         │  Cloud NAT    │                       │
│                         │  (Egress)     │                       │
│                         └───────┬───────┘                       │
└─────────────────────────────────┼───────────────────────────────┘
                                  │
                                  ▼
                          External Services
                          (Benchling, Anthropic)
```

### Firewall Rules

| Rule | Source | Destination | Ports | Action |
|------|--------|-------------|-------|--------|
| Allow IAP | IAP ranges | Cloud Run | 443 | Allow |
| Allow internal | VPC | VPC | All | Allow |
| Deny all | * | * | * | Deny |

### Egress Controls

Outbound traffic allowed to:
- `*.googleapis.com` (GCP services)
- `api.anthropic.com` (AI API)
- `benchling-warehouse.arcinstitute.org` (Benchling)
- `github.com` (Nextflow pipelines)
- `docker.io`, `gcr.io`, `quay.io` (Container images)

## Application Security

### Input Validation

All user input is validated using Pydantic models.

```python
class RunCreateRequest(BaseModel):
    pipeline: str = Field(..., pattern=r"^[a-z-]+/[a-z-]+$")
    pipeline_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    samplesheet_csv: str = Field(..., max_length=10_000_000)
    config_content: str = Field(..., max_length=100_000)
    params: dict[str, Any]
    
    @validator("params")
    def validate_params(cls, v):
        # Custom validation logic
        return v
```

### SQL Injection Prevention

All database queries use parameterized statements.

```python
# Safe: parameterized query
query = text("SELECT * FROM runs WHERE id = :run_id")
result = await session.execute(query, {"run_id": run_id})

# Never: string interpolation
# query = f"SELECT * FROM runs WHERE id = '{run_id}'"  # DANGEROUS
```

### XSS Prevention

- All user content HTML-escaped before display
- Content Security Policy headers set
- No inline JavaScript allowed

### CSRF Protection

- SameSite cookie attribute set to `Strict`
- All state-changing operations require POST
- Origin header validation

## AI Security

### Prompt Injection Protection

```python
def sanitize_user_input(content: str) -> str:
    """Sanitize user input before including in prompts."""
    # Remove potential prompt injection attempts
    dangerous_patterns = [
        r"ignore previous instructions",
        r"disregard.*system prompt",
        r"you are now",
    ]
    
    for pattern in dangerous_patterns:
        content = re.sub(pattern, "[filtered]", content, flags=re.IGNORECASE)
    
    return content
```

### Tool Execution Safety

- All tool parameters validated before execution
- No arbitrary code execution
- Tool results sanitized before display
- Rate limiting on tool calls

### Data Leakage Prevention

- AI never shown other users' data
- Conversation history scoped to session
- No cross-user context sharing

## Audit Logging

### Log Format

```json
{
  "timestamp": "2024-12-18T14:30:00Z",
  "severity": "INFO",
  "service": "arc-nf-platform",
  "user_email": "user@arcinstitute.org",
  "action": "run.submit",
  "resource": "run-abc123",
  "request_id": "req-xyz789",
  "ip_address": "10.0.0.1",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "pipeline": "nf-core/scrnaseq",
    "sample_count": 24
  }
}
```

### Logged Events

| Event | Severity | Details |
|-------|----------|---------|
| User login | INFO | Email, IP |
| Run created | INFO | Run ID, pipeline |
| Run submitted | INFO | Run ID, sample count |
| Run cancelled | INFO | Run ID, user |
| Run failed | WARNING | Run ID, error |
| Auth failure | WARNING | IP, reason |
| Rate limit hit | WARNING | IP, endpoint |
| System error | ERROR | Stack trace |

### Log Retention

| Log Type | Retention |
|----------|-----------|
| Access logs | 90 days |
| Audit logs | 1 year |
| Application logs | 30 days |

## Incident Response

### Security Incident Classification

| Severity | Examples | Response Time |
|----------|----------|---------------|
| Critical | Data breach, unauthorized access | 15 minutes |
| High | Failed auth spike, suspicious activity | 1 hour |
| Medium | Single failed intrusion attempt | 24 hours |
| Low | Policy violation, misconfiguration | 1 week |

### Response Procedures

1. **Detection**: Automated alerts or manual report
2. **Containment**: Isolate affected systems
3. **Investigation**: Analyze logs, identify scope
4. **Remediation**: Fix vulnerability, restore service
5. **Post-mortem**: Document lessons learned

### Emergency Contacts

| Role | Contact |
|------|---------|
| Security Lead | security@arcinstitute.org |
| Platform Lead | platform-team@arcinstitute.org |
| GCP Support | GCP Console |

## Compliance

### Data Handling

- No PHI (Protected Health Information) processed
- No human subjects data without IRB approval
- Research data handling follows Arc policies

### Access Reviews

| Review | Frequency |
|--------|-----------|
| User access | Quarterly |
| Service account permissions | Monthly |
| Secret rotation | Annually |
| Security scan | Weekly |

## Security Checklist

### Pre-Deployment

- [ ] IAP configured and tested
- [ ] Service accounts have minimal permissions
- [ ] Secrets stored in Secret Manager
- [ ] VPC and firewall rules configured
- [ ] Audit logging enabled
- [ ] Vulnerability scan passed

### Ongoing

- [ ] Weekly security scans
- [ ] Monthly access reviews
- [ ] Quarterly penetration testing
- [ ] Annual security training
