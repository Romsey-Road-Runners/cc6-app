variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "domain" {
  description = "The sub-domain to map to the Cloud Run app"
  type        = string
}