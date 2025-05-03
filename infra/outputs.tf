output "project_id" {
  value = var.project_id
}

output "backend_bucket_name" {
  value = google_storage_bucket.backend_bucket.name
}