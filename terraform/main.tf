provider "google" {
  project = var.project_id
  region  = var.region
}

provider "random" {}

provider "docker" {}

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

# Enable Cloud Run API
resource "google_project_service" "cloudrun" {
  service = "run.googleapis.com"
}

# Enable Cloud Build API
resource "google_project_service" "cloudbuild" {
  service = "cloudbuild.googleapis.com"
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

# Build and push Docker image using gcloud
resource "null_resource" "docker_build" {
  provisioner "local-exec" {
    command = <<-EOT
      cd ../parkrun
      gcloud builds submit --project ${var.project_id} --tag gcr.io/${var.project_id}/parkrun-app
    EOT
  }

  depends_on = [google_project_service.cloudbuild]

  triggers = {
    dockerfile_hash = filemd5("../parkrun/Dockerfile")
    app_hash        = filemd5("../parkrun/app.py")
    pipfile_hash    = filemd5("../parkrun/Pipfile")
  }
}

# Create service account for Cloud Run
resource "google_service_account" "cloudrun_sa" {
  account_id   = "parkrun-cloudrun"
  display_name = "Parkrun Cloud Run Service Account"
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

# Deploy Cloud Run service
resource "google_cloud_run_service" "parkrun_app" {
  name     = "parkrun-app"
  location = var.region

  template {
    metadata {
      annotations = {
        "run.googleapis.com/execution-environment" = "gen2"
        "build-trigger"                            = null_resource.docker_build.id
      }
    }

    spec {
      service_account_name = google_service_account.cloudrun_sa.email

      containers {
        image = "gcr.io/${var.project_id}/parkrun-app:latest"

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

  depends_on = [null_resource.docker_build]
}

# Allow unauthenticated access
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.parkrun_app.name
  location = google_cloud_run_service.parkrun_app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Custom domain mapping
resource "google_cloud_run_domain_mapping" "custom_domain" {
  location = var.region
  name     = "api.cc6.co.uk"

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.parkrun_app.name
  }
}

