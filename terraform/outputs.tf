output "firestore_database_name" {
  description = "Name of the Firestore database"
  value       = google_firestore_database.database.name
}

output "cloud_run_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.parkrun_app.status[0].url
}

output "service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_service.parkrun_app.name
}