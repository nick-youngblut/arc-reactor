# Terraform Infrastructure

## Overview
This directory provisions core Arc Reactor infrastructure for a single environment per apply.

## Prerequisites
- Terraform >= 1.5
- GCP project with billing enabled
- A GCS bucket for Terraform state (see `terraform/backend.tf`)
- Service account credentials with IAM permissions to create resources

## Initialize
```bash
cd terraform
terraform init
```

## Plan & Apply
```bash
terraform plan -var-file=environments/dev.tfvars \
  -var "db_password=..." \
  -var "benchling_warehouse_password=..." \
  -var "google_api_key=..."

terraform apply -var-file=environments/dev.tfvars \
  -var "db_password=..." \
  -var "benchling_warehouse_password=..." \
  -var "google_api_key=..."
```

## Notes
- Bucket versioning is enabled at the bucket level. A lifecycle rule deletes `runs/*/work/` objects after 30 days; archived objects are removed after 7 days to provide a soft-delete window.
- IAP requires a serverless NEG and backend service. You still need to attach a HTTPS load balancer and domain mapping for external access.
- Update `terraform/backend.tf` with the actual state bucket name.
- Secrets are stored in Secret Manager via variables. Avoid committing sensitive values in tfvars.
- Create Google Groups for access control (`arc-reactor-users@arcinstitute.org`, `arc-reactor-admins@arcinstitute.org`) in Workspace admin.

## GitHub Actions
Set these repo secrets to enable deployment:
- `GCP_SA_KEY`: service account JSON key
- `GITHUB_TOKEN`: access token for private dependencies
