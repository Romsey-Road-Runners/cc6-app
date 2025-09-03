provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"
}

resource "google_project_service" "appengine" {
  service = "appengine.googleapis.com"
}

# Create App Engine app (required for Firestore)
resource "google_app_engine_application" "app" {
  project     = var.project_id
  location_id = var.region

  depends_on = [google_project_service.appengine]
}

# Create Firestore database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_app_engine_application.app]
}