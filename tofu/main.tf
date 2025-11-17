provider "google" {
  project = var.project_id
  region  = var.region
}

# Generate random secret key
resource "random_password" "flask_secret_key" {
  length  = 32
  special = true
}

# Create secret in Secret Manager
resource "google_secret_manager_secret" "flask_secret_key" {
  secret_id = "flask-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

# Store secret value
resource "google_secret_manager_secret_version" "flask_secret_key" {
  secret      = google_secret_manager_secret.flask_secret_key.id
  secret_data = random_password.flask_secret_key.result
}

# Enable required APIs
resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"
}

resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"
}

# Create Firestore database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.firestore]
}

# Create composite index for participant ordering
resource "google_firestore_index" "participants_name_index" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "participants"

  fields {
    field_path = "last_name"
    order      = "ASCENDING"
  }

  fields {
    field_path = "first_name"
    order      = "ASCENDING"
  }
}

# Create daily backup schedule
resource "google_firestore_backup_schedule" "daily_backup" {
  project   = var.project_id
  database  = google_firestore_database.database.name
  retention = "7776000s" # 90d
  daily_recurrence {}
  depends_on = [google_firestore_database.database]
}

# Enable Cloud Run API
resource "google_project_service" "cloudrun" {
  service = "run.googleapis.com"
}

# Enable Cloud Build API
resource "google_project_service" "cloudbuild" {
  service = "cloudbuild.googleapis.com"
}

# Enable Artifact Registry API (needed for GCR)
resource "google_project_service" "artifactregistry" {
  service = "artifactregistry.googleapis.com"
}


# Placeholder secrets (to be populated manually)
resource "google_secret_manager_secret" "oauth_client_id" {
  secret_id = "oauth-client-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret" "oauth_client_secret" {
  secret_id = "oauth-client-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.secretmanager]
}

# Create service account for Cloud Run
resource "google_service_account" "cloudrun_sa" {
  account_id   = "cc6-app-cloudrun"
  display_name = "CC6 App Cloud Run Service Account"
}

# Create service account for GitHub Actions
resource "google_service_account" "github_actions_sa" {
  account_id   = "cc6-app-github-actions"
  display_name = "CC6 App GitHub Actions Service Account"
}

# Grant Cloud Run deployment permissions to GitHub Actions SA
resource "google_project_iam_member" "github_actions_cloudrun_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

resource "google_project_iam_member" "github_actions_iam_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

resource "google_project_iam_member" "github_actions_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

resource "google_project_iam_member" "github_actions_artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# Create service account key for GitHub Actions
resource "google_service_account_key" "github_actions_key" {
  service_account_id = google_service_account.github_actions_sa.name
}

# Grant access to secrets
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.flask_secret_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "oauth_client_id_access" {
  secret_id = google_secret_manager_secret.oauth_client_id.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "oauth_client_secret_access" {
  secret_id = google_secret_manager_secret.oauth_client_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant Firestore access
resource "google_project_iam_member" "firestore_access" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Deploy Cloud Run service for monolithic app
locals {
  monolithic_app_count = var.domain_monolithic_app != "" ? 1 : 0
}

resource "google_cloud_run_service" "app" {
  count    = local.monolithic_app_count
  name     = "cc6-app"
  location = var.region

  template {
    metadata {
      annotations = {
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/startup-cpu-boost"     = "true"
      }
    }

    spec {
      service_account_name = google_service_account.cloudrun_sa.email

      containers {
        image = "gcr.io/${var.project_id}/app:latest"

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        env {
          name = "FLASK_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.flask_secret_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.oauth_client_id.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.oauth_client_secret.secret_id
              key  = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"]
    ]
  }
}

# Allow unauthenticated access
resource "google_cloud_run_service_iam_member" "public_access" {
  count    = local.monolithic_app_count
  service  = google_cloud_run_service.app.0.name
  location = google_cloud_run_service.app.0.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Custom domain mapping
resource "google_cloud_run_domain_mapping" "custom_domain" {
  count    = local.monolithic_app_count
  location = var.region
  name     = var.domain_monolithic_app

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.app.0.name
  }
}

# Public API
resource "google_cloud_run_service" "api" {
  name     = "api"
  location = var.region

  template {
    metadata {
      annotations = {
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/startup-cpu-boost"     = "true"
      }
    }

    spec {
      service_account_name = google_service_account.cloudrun_sa.email

      containers {
        image = "gcr.io/${var.project_id}/api:latest"

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        env {
          name = "FLASK_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.flask_secret_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.oauth_client_id.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.oauth_client_secret.secret_id
              key  = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"]
    ]
  }
}

resource "google_cloud_run_service_iam_member" "api_public_access" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_domain_mapping" "api_custom_domain" {
  location = var.region
  name     = var.domain_api

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.api.name
  }
}

# Public API
resource "google_cloud_run_service" "admin" {
  name     = "admin"
  location = var.region

  template {
    metadata {
      annotations = {
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/startup-cpu-boost"     = "true"
      }
    }

    spec {
      service_account_name = google_service_account.cloudrun_sa.email

      containers {
        image = "gcr.io/${var.project_id}/admin:latest"

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        env {
          name = "FLASK_SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.flask_secret_key.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_CLIENT_ID"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.oauth_client_id.secret_id
              key  = "latest"
            }
          }
        }

        env {
          name = "GOOGLE_CLIENT_SECRET"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.oauth_client_secret.secret_id
              key  = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].spec[0].containers[0].image,
      template[0].metadata[0].annotations["run.googleapis.com/client-name"],
      template[0].metadata[0].annotations["run.googleapis.com/client-version"]
    ]
  }
}

resource "google_cloud_run_service_iam_member" "admin_public_access" {
  service  = google_cloud_run_service.admin.name
  location = google_cloud_run_service.admin.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_domain_mapping" "admin_custom_domain" {
  location = var.region
  name     = var.domain_admin

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.admin.name
  }
}

# Output the service account key for GitHub Actions
output "github_actions_service_account_key" {
  value     = base64decode(google_service_account_key.github_actions_key.private_key)
  sensitive = true
}
