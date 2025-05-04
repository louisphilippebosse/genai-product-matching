resource "google_service_account" "cloud_run_service_account" {
  account_id   = "cloud-run-service-account"
  display_name = "Service Account for Cloud Run"
}

resource "google_project_iam_member" "cloud_run_service_account_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}



resource "google_artifact_registry_repository" "product_matching_app" {
  repository_id = "product-matching-app"
  format        = "DOCKER"
  location      = "northamerica-northeast1"
  description   = "Artifact Registry repository for the Product Matching app"
}

resource "google_cloud_run_v2_service" "flask_app" {
  depends_on = [
    google_artifact_registry_repository.product_matching_app,
    google_service_account.cloud_run_service_account
  ]
  name     = "product-matching-app"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "northamerica-northeast1-docker.pkg.dev/${var.project_id}/product-matching-app/product-matching-app:v1.0.0"
      ports {
        name = "http"
        container_port = 5000
      }
      resources {
        limits = {
          memory = "512Mi"
          cpu    = "1"
        }
      }
    }
    service_account = google_service_account.cloud_run_service_account.email
    scaling {
      max_instance_count = 2
    }  
  }

  traffic {
    percent = 100
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role    = "roles/run.invoker"
    members = ["allUsers"]
  }
}

resource "google_cloud_run_v2_service_iam_policy" "noauth" {
  project     = var.project_id
  location    = google_cloud_run_v2_service.flask_app.location
  name        = google_cloud_run_v2_service.flask_app.name
  policy_data = data.google_iam_policy.noauth.policy_data
}