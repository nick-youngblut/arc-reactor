project_id   = "arc-ctc-project"
region       = "us-west1"
environment  = "prod"
service_name = "arc-reactor"
image        = "us-west1-docker.pkg.dev/arc-ctc-project/arc-reactor/arc-reactor:prod"
runs_bucket  = "arc-reactor-runs"

db_instance_name = "arc-reactor-db"
db_name          = "arc_reactor_prod"

# Set via -var or TF_VAR_* env vars for local runs
# db_password = ""
# benchling_prod_api_key = ""
# benchling_prod_database_uri = ""
# benchling_prod_app_client_id = ""
# benchling_prod_app_client_secret = ""
# google_api_key = ""
