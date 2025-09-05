output "firestore_database_name" {
  description = "Name of the Firestore database"
  value       = google_firestore_database.database.name
}

output "cloud_run_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.api_app.status[0].url
}

output "service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_service.api_app.name
}

output "custom_domain_dns" {
  description = "DNS record needed for custom domain"
  value       = "CNAME api.cc6.co.uk -> ${google_cloud_run_domain_mapping.custom_domain.status[0].resource_records[0].rrdata}"
}

