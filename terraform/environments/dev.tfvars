project_id   = "arc-ctc-project"
region       = "us-west1"
environment  = "test"
service_name = "arc-reactor-dev"
image        = "us-west1-docker.pkg.dev/arc-ctc-project/arc-reactor/arc-reactor:dev"
runs_bucket  = "arc-reactor-runs-dev"

db_instance_name = "arc-reactor-db-dev"
db_name          = "arc_reactor_dev"

# Set via -var or TF_VAR_* env vars for local runs
# db_password = ""
# benchling_test_api_key = ""
# benchling_test_database_uri = ""
# benchling_test_app_client_id = ""
# benchling_test_app_client_secret = ""
# google_api_key = ""
