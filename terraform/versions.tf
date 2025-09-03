terraform {
  backend "gcs" {
    bucket = "${var.project_id}-tofu-state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
  required_version = ">= 1.10"
}