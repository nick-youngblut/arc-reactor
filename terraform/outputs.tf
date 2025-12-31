output "cloud_run_service" {
  value = google_cloud_run_v2_service.app.name
}

output "cloud_run_uri" {
  value = google_cloud_run_v2_service.app.uri
}

output "runs_bucket" {
  value = google_storage_bucket.runs.name
}

output "service_accounts" {
  value = {
    app          = google_service_account.app.email
    orchestrator = google_service_account.orchestrator.email
    tasks        = google_service_account.tasks.email
  }
}

output "cloud_sql_instance" {
  value = google_sql_database_instance.main.name
}
