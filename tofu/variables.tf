variable "project_id" {
  description = "Google Cloud Project ID"
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