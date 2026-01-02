terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.20"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.20"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

locals {
  required_apis = [
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "batch.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "iap.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com"
  ]

  app_roles = [
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/storage.objectViewer",
    "roles/batch.jobsEditor",
    "roles/logging.logWriter",
    "roles/secretmanager.secretAccessor"
  ]

  orchestrator_roles = [
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/storage.objectViewer",
    "roles/batch.jobsEditor",
    "roles/logging.logWriter"
  ]

  task_roles = [
    "roles/storage.objectAdmin",
    "roles/storage.objectViewer",
    "roles/logging.logWriter"
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.required_apis)
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "vpc" {
  name                    = var.vpc_name
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "subnet" {
  name          = var.subnet_name
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
}

resource "google_compute_global_address" "private_service_range" {
  name          = "arc-reactor-private-services"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_range.name]
}

resource "google_vpc_access_connector" "connector" {
  name          = var.vpc_connector_name
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = var.vpc_connector_cidr
}

resource "google_compute_router" "router" {
  name    = var.router_name
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = var.nat_name
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

resource "google_compute_firewall" "allow_iap" {
  name    = "allow-iap-ingress"
  network = google_compute_network.vpc.name

  direction = "INGRESS"
  source_ranges = [
    "35.235.240.0/20"
  ]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

resource "google_compute_firewall" "allow_internal" {
  name    = "allow-internal-ingress"
  network = google_compute_network.vpc.name

  direction     = "INGRESS"
  source_ranges = ["10.0.0.0/8"]

  allow {
    protocol = "all"
  }
}

resource "google_service_account" "app" {
  account_id   = "arc-reactor"
  display_name = "Arc Reactor Cloud Run"
}

resource "google_service_account" "orchestrator" {
  account_id   = "nextflow-orchestrator"
  display_name = "Nextflow Orchestrator"
}

resource "google_service_account" "tasks" {
  account_id   = "nextflow-tasks"
  display_name = "Nextflow Tasks"
}

resource "google_project_iam_member" "app_roles" {
  for_each = toset(local.app_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "orchestrator_roles" {
  for_each = toset(local.orchestrator_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.orchestrator.email}"
}

resource "google_project_iam_member" "task_roles" {
  for_each = toset(local.task_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.tasks.email}"
}

resource "google_secret_manager_secret" "benchling_prod_api_key" {
  secret_id = "benchling-prod-api-key"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "benchling_prod_api_key" {
  secret      = google_secret_manager_secret.benchling_prod_api_key.id
  secret_data = var.benchling_prod_api_key
}

resource "google_secret_manager_secret" "benchling_prod_database_uri" {
  secret_id = "benchling-prod-database-uri"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "benchling_prod_database_uri" {
  secret      = google_secret_manager_secret.benchling_prod_database_uri.id
  secret_data = var.benchling_prod_database_uri
}

resource "google_secret_manager_secret" "benchling_prod_app_client_id" {
  secret_id = "benchling-prod-app-client-id"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "benchling_prod_app_client_id" {
  secret      = google_secret_manager_secret.benchling_prod_app_client_id.id
  secret_data = var.benchling_prod_app_client_id
}

resource "google_secret_manager_secret" "benchling_prod_app_client_secret" {
  secret_id = "benchling-prod-app-client-secret"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "benchling_prod_app_client_secret" {
  secret      = google_secret_manager_secret.benchling_prod_app_client_secret.id
  secret_data = var.benchling_prod_app_client_secret
}

resource "google_secret_manager_secret" "benchling_test_api_key" {
  secret_id = "benchling-test-api-key"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "benchling_test_api_key" {
  secret      = google_secret_manager_secret.benchling_test_api_key.id
  secret_data = var.benchling_test_api_key
}

resource "google_secret_manager_secret" "benchling_test_database_uri" {
  secret_id = "benchling-test-database-uri"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "benchling_test_database_uri" {
  secret      = google_secret_manager_secret.benchling_test_database_uri.id
  secret_data = var.benchling_test_database_uri
}

resource "google_secret_manager_secret" "benchling_test_app_client_id" {
  secret_id = "benchling-test-app-client-id"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "benchling_test_app_client_id" {
  secret      = google_secret_manager_secret.benchling_test_app_client_id.id
  secret_data = var.benchling_test_app_client_id
}

resource "google_secret_manager_secret" "benchling_test_app_client_secret" {
  secret_id = "benchling-test-app-client-secret"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "benchling_test_app_client_secret" {
  secret      = google_secret_manager_secret.benchling_test_app_client_secret.id
  secret_data = var.benchling_test_app_client_secret
}

resource "google_secret_manager_secret" "google_api_key" {
  secret_id = "google-api-key"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "google_api_key" {
  secret      = google_secret_manager_secret.google_api_key.id
  secret_data = var.google_api_key
}

resource "google_storage_bucket" "runs" {
  name                        = var.runs_bucket
  location                    = var.region
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age            = 30
      matches_prefix = ["runs/*/work/"]
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age            = 7
      with_state     = "ARCHIVED"
      matches_prefix = ["runs/"]
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket_iam_member" "runs_admin_app" {
  bucket = google_storage_bucket.runs.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.app.email}"
}

resource "google_storage_bucket_iam_member" "runs_admin_orchestrator" {
  bucket = google_storage_bucket.runs.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.orchestrator.email}"
}

resource "google_storage_bucket_iam_member" "runs_admin_tasks" {
  bucket = google_storage_bucket.runs.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.tasks.email}"
}

resource "google_sql_database_instance" "main" {
  name             = var.db_instance_name
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = true

  settings {
    tier = var.db_tier

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "app" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "app" {
  instance = google_sql_database_instance.main.name
  name     = var.db_user
  password = var.db_password
}

resource "google_cloud_run_v2_service" "app" {
  name     = var.service_name
  location = var.region
  ingress  = var.cloud_run_ingress

  template {
    service_account = google_service_account.app.email

    containers {
      image = var.image

      env {
        name  = "DYNACONF"
        value = var.environment
      }

      env {
        name  = "FRONTEND_OUT_DIR"
        value = "/app/frontend/out"
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

      env {
        name = "GOOGLE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_api_key.id
            version = "latest"
          }
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_compute_region_network_endpoint_group" "app" {
  name                  = "arc-reactor-neg"
  region                = var.region
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = google_cloud_run_v2_service.app.name
  }
}

resource "google_iap_brand" "iap_brand" {
  provider     = google-beta
  support_email = var.iap_support_email
  application_title = "Arc Reactor"
}

resource "google_iap_client" "iap_client" {
  provider     = google-beta
  display_name = "Arc Reactor"
  brand        = google_iap_brand.iap_brand.name
}

resource "google_compute_backend_service" "app" {
  name                  = "arc-reactor-backend"
  protocol              = "HTTP"
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.app.id
  }

  iap {
    oauth2_client_id     = google_iap_client.iap_client.client_id
    oauth2_client_secret = google_iap_client.iap_client.secret
  }
}

resource "google_iap_web_backend_service_iam_binding" "iap_access" {
  web_backend_service = google_compute_backend_service.app.name
  role                = "roles/iap.httpsResourceAccessor"
  members             = ["group:${var.iap_access_group}"]
}
