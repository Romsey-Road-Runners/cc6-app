resource "google_artifact_registry_repository" "api_repo" {
  location      = "us"
  repository_id = "gcr.io"
  description   = "Docker repository for API"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-recent-versions"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }

  cleanup_policies {
    id     = "delete-untagged"
    action = "DELETE"
    condition {
      tag_state = "UNTAGGED"
    }
  }
}