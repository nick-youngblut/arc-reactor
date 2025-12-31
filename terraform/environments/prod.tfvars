project_id   = "arc-ctc-project"
region       = "us-west1"
environment  = "production"
service_name = "arc-reactor"
image        = "us-west1-docker.pkg.dev/arc-ctc-project/arc-reactor/arc-reactor:prod"
runs_bucket  = "arc-reactor-runs"

db_instance_name = "arc-reactor-db"
db_name          = "arc_reactor_prod"

# Set via -var or TF_VAR_* env vars for local runs
# db_password = ""
# benchling_warehouse_password = ""
# google_api_key = ""
