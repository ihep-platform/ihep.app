# =============================================================================
# IHEP Platform - Mirth Connect Infrastructure Variables
# =============================================================================
# Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
# =============================================================================

# -----------------------------------------------------------------------------
# Project Settings
# -----------------------------------------------------------------------------
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

# -----------------------------------------------------------------------------
# Cloud Run Settings
# -----------------------------------------------------------------------------
variable "cloud_run_cpu" {
  description = "CPU limit for Mirth Connect Cloud Run instances"
  type        = string
  default     = "2"
}

variable "cloud_run_memory" {
  description = "Memory limit for Mirth Connect Cloud Run instances"
  type        = string
  default     = "2Gi"
}

variable "cloud_run_min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 1
}

variable "cloud_run_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 5
}

variable "mirth_image_tag" {
  description = "Docker image tag for Mirth Connect"
  type        = string
  default     = "4.5.0"
}

variable "ehr_gateway_image_tag" {
  description = "Docker image tag for EHR Integration Gateway"
  type        = string
  default     = "latest"
}

# -----------------------------------------------------------------------------
# Cloud SQL Settings
# -----------------------------------------------------------------------------
variable "cloud_sql_tier" {
  description = "Cloud SQL machine tier"
  type        = string
  default     = "db-custom-2-4096"
}

variable "cloud_sql_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 20
}

variable "mirth_db_name" {
  description = "Database name for Mirth Connect"
  type        = string
  default     = "mirthdb"
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------
variable "vpc_network_id" {
  description = "VPC network self-link for Cloud SQL private IP"
  type        = string
}

variable "vpc_network_name" {
  description = "VPC network name for VPC Access Connector"
  type        = string
}

variable "vpc_connector_cidr" {
  description = "CIDR range for VPC Access Connector"
  type        = string
  default     = "10.8.0.0/28"
}

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
variable "kms_key_id" {
  description = "KMS key ID for encryption (Cloud Storage, etc.)"
  type        = string
  default     = ""
}

variable "ehr_partner_secret_names" {
  description = "List of EHR partner secret names to create in Secret Manager"
  type        = list(string)
  default = [
    "epic-client-id",
    "epic-client-secret",
    "cerner-client-id",
    "cerner-client-secret",
    "allscripts-api-key",
    "allscripts-app-name",
    "athena-client-id",
    "athena-client-secret",
    "athena-practice-id",
  ]
}

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------
variable "alert_notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

# -----------------------------------------------------------------------------
# Labels
# -----------------------------------------------------------------------------
variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    project   = "ihep"
    managed   = "terraform"
    component = "ehr-integration"
  }
}
