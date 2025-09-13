# Create bucket for storing Terraform state
resource "google_storage_bucket" "terraform_state" {
  name     = "${var.project_id}-tofu-state"
  location = var.region

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }
}