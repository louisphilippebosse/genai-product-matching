resource "google_artifact_registry_repository" "product_matching_app" {
  name         = "product-matching-app"
  repository_id = "product-matching-app"
  format       = "DOCKER"
  location     = "northamerica-northeast1"
  description  = "Artifact Registry repository for the Product Matching app"
}
# resource "google_cloud_run_service" "flask_app" {
#   name     = "product-matching-app"
#   location = var.region

#   template {
#     spec {
#       containers {
#         image = "gcr.io/${var.project_id}/product-matching-app:latest"
#         ports {
#           container_port = 5000
#         }
#         resources {
#           limits = {
#             memory = "512Mi"
#             cpu    = "1"
#           }
#         }
#       }
#     }
#   }

#   traffic {
#     percent         = 100
#     latest_revision = true
#   }
# }

# resource "google_cloud_run_service_iam_policy" "noauth" {
#   location    = google_cloud_run_service.flask_app.location
#   service     = google_cloud_run_service.flask_app.name
#   policy_data = data.google_iam_policy.noauth.policy_data
# }

# data "google_iam_policy" "noauth" {
#   binding {
#     role    = "roles/run.invoker"
#     members = ["allUsers"]
#   }
# }