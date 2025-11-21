variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "firebase_site_suffix" {
  description = "As the firebase site id must be globally unique, configure a suffix"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}


variable "domain_monolithic_app" {
  description = "Domain used for monolithic app"
  type        = string
  default     = ""
}

variable "domain_api" {
  description = "Domain used for api"
  type        = string
}

variable "domain_admin" {
  description = "Domain used for admin app"
  type        = string
}

variable "domain_frontend" {
  description = "Domain used for frontend app (Firebase Hosting)"
  type        = string
}

