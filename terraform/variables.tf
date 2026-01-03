variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
  default     = "us-west1"
}

variable "environment" {
  type        = string
  description = "Environment name (development|production)"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name"
}

variable "frontend_image" {
  description = "Container image for frontend service"
  type        = string
}

variable "backend_image" {
  description = "Container image for backend service"
  type        = string
}

variable "weblog_receiver_image" {
  description = "Container image for weblog receiver service"
  type        = string
}

variable "database_url" {
  description = "PostgreSQL database connection URL"
  type        = string
  sensitive   = true
}

variable "runs_bucket" {
  type        = string
  description = "GCS bucket for pipeline runs"
}

variable "vpc_name" {
  type        = string
  default     = "arc-reactor-vpc"
}

variable "subnet_name" {
  type        = string
  default     = "arc-reactor-subnet"
}

variable "subnet_cidr" {
  type        = string
  default     = "10.10.0.0/24"
}

variable "vpc_connector_name" {
  type        = string
  default     = "arc-reactor-connector"
}

variable "vpc_connector_cidr" {
  type        = string
  default     = "10.8.0.0/28"
}

variable "router_name" {
  type        = string
  default     = "arc-reactor-router"
}

variable "nat_name" {
  type        = string
  default     = "arc-reactor-nat"
}

variable "db_instance_name" {
  type        = string
  description = "Cloud SQL instance name"
}

variable "db_tier" {
  type        = string
  default     = "db-f1-micro"
}

variable "db_name" {
  type        = string
  description = "Database name"
}

variable "db_user" {
  type        = string
  description = "Database user"
  default     = "arc_reactor"
}

variable "db_password" {
  type        = string
  description = "Database password"
  sensitive   = true
}

variable "benchling_prod_api_key" {
  type        = string
  description = "Benchling prod API key"
  sensitive   = true
}

variable "benchling_prod_database_uri" {
  type        = string
  description = "Benchling prod database URI"
  sensitive   = true
}

variable "benchling_prod_app_client_id" {
  type        = string
  description = "Benchling prod app client ID"
  sensitive   = true
}

variable "benchling_prod_app_client_secret" {
  type        = string
  description = "Benchling prod app client secret"
  sensitive   = true
}

variable "benchling_test_api_key" {
  type        = string
  description = "Benchling test API key"
  sensitive   = true
}

variable "benchling_test_database_uri" {
  type        = string
  description = "Benchling test database URI"
  sensitive   = true
}

variable "benchling_test_app_client_id" {
  type        = string
  description = "Benchling test app client ID"
  sensitive   = true
}

variable "benchling_test_app_client_secret" {
  type        = string
  description = "Benchling test app client secret"
  sensitive   = true
}

variable "google_api_key" {
  type        = string
  description = "Google AI API key"
  sensitive   = true
}

variable "iap_support_email" {
  type        = string
  description = "Support email for IAP brand"
  default     = "security@arcinstitute.org"
}

variable "iap_access_group" {
  type        = string
  description = "Google group with IAP access"
  default     = "arc-reactor-users@arcinstitute.org"
}

variable "cloud_run_ingress" {
  type        = string
  description = "Cloud Run ingress setting"
  default     = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
}
