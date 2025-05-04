terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.33.0" # Use the latest compatible version
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}