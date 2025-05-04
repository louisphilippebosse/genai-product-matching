resource "google_service_account" "cloud_run_service_account" {
  account_id   = "cloud-run-service-account"
  display_name = "Service Account for Cloud Run"
}

resource "google_project_iam_member" "cloud_run_service_account_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

resource "google_storage_bucket_iam_member" "cloud_run_service_account_storage_reader" {
  bucket = google_storage_bucket.data_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

resource "google_project_iam_member" "cloud_run_service_account_vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}
resource "google_project_iam_member" "cloud_run_service_account_vertex_ai_indexer" {
  project = var.project_id
  role    = "roles/aiplatform.indexer"
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
        name = "http1"
        container_port = 5000
      }
      resources {
        limits = {
          memory = "2Gi"
          cpu    = "2"
        }
      }
      startup_probe {
        timeout_seconds   = 5
        period_seconds    = 15
        failure_threshold = 3
        tcp_socket {
          port = 5000
        }
      }
    }
    service_account = google_service_account.cloud_run_service_account.email
    scaling {
      max_instance_count = 2
    }  
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

resource "google_storage_bucket" "data_bucket" {
  name          = "${var.project_id}-data"
  location      = var.region
  storage_class = "STANDARD"

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365
    }
  }
}


# Create the Vertex AI Index
resource "google_vertex_ai_index" "product_matching_index" {
  display_name = "product-matching-index"
  description  = "Index for product matching"
  region       = var.region

  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.data_bucket.name}/contents/internal_products.jsonl"

    config {
      dimensions = 768  # Adjust based on your embedding size
      approximate_neighbors_count = 100
      shard_size = "SHARD_SIZE_SMALL"
      distance_measure_type = "DOT_PRODUCT_DISTANCE"

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 500
          leaf_nodes_to_search_percent = 7
        }
      }
    }
  }

  index_update_method = "BATCH_UPDATE"
}

# Deploy the Vertex AI Index to an Endpoint
resource "google_vertex_ai_index_endpoint" "product_matching_endpoint" {
  display_name = "product-matching-endpoint"
  region       = var.region
}

resource "google_vertex_ai_index_endpoint_deployed_index" "product_matching_deployment" {
  depends_on = [
    google_vertex_ai_index.product_matching_index,
    google_vertex_ai_index_endpoint.product_matching_endpoint
  ]
  index_endpoint = google_vertex_ai_index_endpoint.product_matching_endpoint.id
  deployed_index {
    id    = "product-matching-deployment"
    index = google_vertex_ai_index.product_matching_index.id
  }
}