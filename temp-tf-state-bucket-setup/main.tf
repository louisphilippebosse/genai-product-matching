provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "backend_bucket" {
  name     = "${var.project_id}-terraform-state"
  location = var.region

  versioning {
    enabled = true
  }
}