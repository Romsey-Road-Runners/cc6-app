output "firestore_database_name" {
  description = "Name of the Firestore database"
  value       = google_firestore_database.database.name
}

output "app_engine_url" {
  description = "App Engine application URL"
  value       = "https://${var.project_id}.appspot.com"
}