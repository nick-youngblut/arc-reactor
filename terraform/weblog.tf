# Weblog receiver service account
resource "google_service_account" "weblog" {
  account_id   = "arc-reactor-weblog"
  display_name = "Arc Reactor Weblog Receiver"
}

resource "google_project_iam_member" "weblog_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.weblog.email}"
}

# Pub/Sub topic for weblog events
resource "google_pubsub_topic" "weblog_events" {
  name = "arc-reactor-weblog-events"
  message_retention_duration = "604800s"
}

# Dead letter topic
resource "google_pubsub_topic" "weblog_dlq" {
  name = "arc-reactor-weblog-events-dlq"
}

# Pub/Sub service account
resource "google_service_account" "pubsub" {
  account_id   = "arc-reactor-pubsub"
  display_name = "Arc Reactor Pub/Sub Push"
}

# Pub/Sub push subscription
resource "google_pubsub_subscription" "weblog_push" {
  name  = "arc-reactor-weblog-push"
  topic = google_pubsub_topic.weblog_events.id

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.backend.uri}/api/internal/weblog"

    oidc_token {
      service_account_email = google_service_account.pubsub.email
      audience              = "${google_cloud_run_v2_service.backend.uri}/api/internal/weblog"
    }
  }

  enable_message_ordering = true
  ack_deadline_seconds    = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.weblog_dlq.id
    max_delivery_attempts = 5
  }
}

# Grant Pub/Sub SA permission to invoke backend
resource "google_cloud_run_v2_service_iam_member" "pubsub_invoker" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub.email}"
}

# Cloud Scheduler service account
resource "google_service_account" "scheduler" {
  account_id   = "arc-reactor-scheduler"
  display_name = "Arc Reactor Cloud Scheduler"
}

# Grant Scheduler SA permission to invoke backend
resource "google_cloud_run_v2_service_iam_member" "scheduler_invoker" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

# Cloud Scheduler job for stale run reconciliation
resource "google_cloud_scheduler_job" "reconcile" {
  name        = "arc-reactor-reconcile-runs"
  description = "Reconcile stale runs every 5 minutes"
  schedule    = "*/5 * * * *"
  time_zone   = "America/Los_Angeles"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.backend.uri}/api/internal/reconcile-runs"

    oidc_token {
      service_account_email = google_service_account.scheduler.email
      audience              = "${google_cloud_run_v2_service.backend.uri}/api/internal/reconcile-runs"
    }
  }

  retry_config {
    retry_count = 3
  }
}

# Weblog receiver Cloud Run service
resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = var.database_url
}

resource "google_cloud_run_v2_service" "weblog_receiver" {
  name     = "arc-reactor-weblog"
  location = var.region

  template {
    service_account = google_service_account.weblog.email

    containers {
      image = var.weblog_receiver_image

      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }

      env {
        name  = "PUBSUB_TOPIC"
        value = google_pubsub_topic.weblog_events.name
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.id
            version = "latest"
          }
        }
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }
  }

  ingress = "INGRESS_TRAFFIC_ALL"
}

# Allow unauthenticated access to weblog receiver
resource "google_cloud_run_v2_service_iam_member" "weblog_public" {
  name     = google_cloud_run_v2_service.weblog_receiver.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output the weblog receiver URL
output "weblog_receiver_url" {
  value = google_cloud_run_v2_service.weblog_receiver.uri
}
