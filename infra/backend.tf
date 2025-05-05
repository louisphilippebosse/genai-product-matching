terraform {
  backend "gcs" {
    bucket  = "genai-product-matching-terraform-state"
    prefix  = "terraform/state"
  }
}