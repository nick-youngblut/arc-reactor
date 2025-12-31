terraform {
  backend "gcs" {
    bucket = "arc-reactor-terraform-state"
    prefix = "terraform/state"
  }
}
