# =============================================================================
# IHEP Platform - Mirth Connect Infrastructure (GCP)
# =============================================================================
# Deploys Mirth Connect integration engine on Google Cloud Platform
# with Cloud Run, Cloud SQL, Pub/Sub, and supporting services.
#
# Author: Jason M Jarmacz | Co-Author: Claude by Anthropic
# =============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# -----------------------------------------------------------------------------
# Cloud Run - Mirth Connect Service
# -----------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "mirth_connect" {
  name     = "ihep-mirth-connect-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "nextgenhealthcare/connect:${var.mirth_image_tag}"

      ports {
        container_port = 8443
      }

      env {
        name  = "DATABASE"
        value = "postgres"
      }
      env {
        name  = "DATABASE_URL"
        value = "jdbc:postgresql:///${var.mirth_db_name}?cloudSqlInstance=${var.project_id}:${var.region}:${google_sql_database_instance.mirth_db.name}&socketFactory=com.google.cloud.sql.postgres.SocketFactory"
      }
      env {
        name = "DATABASE_USERNAME"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.mirth_db_user.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DATABASE_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.mirth_db_password.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "DATABASE_MAX_CONNECTIONS"
        value = "20"
      }
      env {
        name  = "IHEP_GATEWAY_URL"
        value = "http://ehr-integration-service:8093/api/v1/ehr"
      }
      env {
        name  = "IHEP_ENVIRONMENT"
        value = var.environment
      }

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }

      startup_probe {
        http_get {
          path = "/api/system/stats"
          port = 8443
        }
        initial_delay_seconds = 60
        period_seconds        = 10
        failure_threshold     = 10
      }

      liveness_probe {
        http_get {
          path = "/api/system/stats"
          port = 8443
        }
        period_seconds    = 30
        failure_threshold = 3
      }
    }

    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.mirth_connector.id
      egress    = "ALL_TRAFFIC"
    }

    service_account = google_service_account.mirth_sa.email

    labels = merge(var.labels, {
      service     = "mirth-connect"
      component   = "ehr-integration"
      environment = var.environment
    })
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_sql_database.mirth_database,
    google_secret_manager_secret_version.mirth_db_user_version,
    google_secret_manager_secret_version.mirth_db_password_version,
  ]
}

# -----------------------------------------------------------------------------
# Cloud Run - EHR Integration Gateway Service
# -----------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "ehr_integration_gateway" {
  name     = "ihep-ehr-integration-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "gcr.io/${var.project_id}/ehr-integration-gateway:${var.ehr_gateway_image_tag}"

      ports {
        container_port = 8093
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "PUBSUB_EHR_INBOUND_TOPIC"
        value = google_pubsub_topic.ehr_inbound.name
      }
      env {
        name  = "PUBSUB_EHR_OUTBOUND_TOPIC"
        value = google_pubsub_topic.ehr_outbound.name
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "1Gi"
        }
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    vpc_access {
      connector = google_vpc_access_connector.mirth_connector.id
      egress    = "ALL_TRAFFIC"
    }

    service_account = google_service_account.mirth_sa.email
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# -----------------------------------------------------------------------------
# Cloud SQL - PostgreSQL for Mirth Connect
# -----------------------------------------------------------------------------
resource "google_sql_database_instance" "mirth_db" {
  name             = "ihep-mirth-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  settings {
    tier              = var.cloud_sql_tier
    disk_size         = var.cloud_sql_disk_size
    disk_autoresize   = true
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = var.environment == "production"
      start_time                     = "03:00"
      transaction_log_retention_days = 7

      backup_retention_settings {
        retained_backups = 30
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_network_id
      require_ssl     = true
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    maintenance_window {
      day          = 7 # Sunday
      hour         = 4
      update_track = "stable"
    }

    user_labels = merge(var.labels, {
      service = "mirth-connect"
    })
  }

  deletion_protection = var.environment == "production"
}

resource "google_sql_database" "mirth_database" {
  name     = var.mirth_db_name
  instance = google_sql_database_instance.mirth_db.name
  project  = var.project_id
}

resource "google_sql_user" "mirth_user" {
  name     = "mirth"
  instance = google_sql_database_instance.mirth_db.name
  password = random_password.mirth_db_password.result
  project  = var.project_id
}

resource "random_password" "mirth_db_password" {
  length  = 32
  special = true
}

# -----------------------------------------------------------------------------
# Cloud Storage - Message Attachments
# -----------------------------------------------------------------------------
resource "google_storage_bucket" "mirth_attachments" {
  name          = "ihep-mirth-attachments-${var.project_id}-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "production"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 730 # 2 years
    }
    action {
      type = "Delete"
    }
  }

  encryption {
    default_kms_key_name = var.kms_key_id
  }

  labels = merge(var.labels, {
    service = "mirth-connect"
  })
}

# -----------------------------------------------------------------------------
# Pub/Sub - Async Event Processing
# -----------------------------------------------------------------------------
resource "google_pubsub_topic" "ehr_inbound" {
  name    = "ihep-ehr-inbound-events-${var.environment}"
  project = var.project_id

  message_retention_duration = "604800s" # 7 days

  labels = merge(var.labels, {
    direction = "inbound"
  })
}

resource "google_pubsub_topic" "ehr_outbound" {
  name    = "ihep-ehr-outbound-events-${var.environment}"
  project = var.project_id

  message_retention_duration = "604800s"

  labels = merge(var.labels, {
    direction = "outbound"
  })
}

resource "google_pubsub_topic" "ehr_sync_requests" {
  name    = "ihep-ehr-sync-requests-${var.environment}"
  project = var.project_id

  message_retention_duration = "604800s"

  labels = merge(var.labels, {
    direction = "sync"
  })
}

resource "google_pubsub_subscription" "ehr_inbound_sub" {
  name    = "ihep-ehr-inbound-processor-${var.environment}"
  topic   = google_pubsub_topic.ehr_inbound.id
  project = var.project_id

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.ehr_dead_letter.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_subscription" "ehr_outbound_sub" {
  name    = "ihep-ehr-outbound-processor-${var.environment}"
  topic   = google_pubsub_topic.ehr_outbound.id
  project = var.project_id

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

resource "google_pubsub_topic" "ehr_dead_letter" {
  name    = "ihep-ehr-dead-letter-${var.environment}"
  project = var.project_id

  labels = merge(var.labels, {
    type = "dead-letter"
  })
}

# -----------------------------------------------------------------------------
# Secret Manager - EHR Partner Credentials
# -----------------------------------------------------------------------------
resource "google_secret_manager_secret" "mirth_db_user" {
  secret_id = "ihep-mirth-db-user-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = merge(var.labels, {
    service = "mirth-connect"
  })
}

resource "google_secret_manager_secret_version" "mirth_db_user_version" {
  secret      = google_secret_manager_secret.mirth_db_user.id
  secret_data = "mirth"
}

resource "google_secret_manager_secret" "mirth_db_password" {
  secret_id = "ihep-mirth-db-password-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = merge(var.labels, {
    service = "mirth-connect"
  })
}

resource "google_secret_manager_secret_version" "mirth_db_password_version" {
  secret      = google_secret_manager_secret.mirth_db_password.id
  secret_data = random_password.mirth_db_password.result
}

# EHR partner credential secrets (created empty, populated manually)
resource "google_secret_manager_secret" "ehr_partner_secrets" {
  for_each  = toset(var.ehr_partner_secret_names)
  secret_id = "ihep-ehr-${each.key}-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = merge(var.labels, {
    service = "ehr-integration"
    type    = "partner-credential"
  })
}

# -----------------------------------------------------------------------------
# VPC Access Connector
# -----------------------------------------------------------------------------
resource "google_vpc_access_connector" "mirth_connector" {
  name          = "ihep-mirth-vpc-${var.environment}"
  project       = var.project_id
  region        = var.region
  network       = var.vpc_network_name
  ip_cidr_range = var.vpc_connector_cidr
  machine_type  = "e2-micro"

  min_instances = 2
  max_instances = 3
}

# -----------------------------------------------------------------------------
# Service Account & IAM
# -----------------------------------------------------------------------------
resource "google_service_account" "mirth_sa" {
  account_id   = "ihep-mirth-connect-${var.environment}"
  display_name = "IHEP Mirth Connect Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "mirth_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.mirth_sa.email}"
}

resource "google_project_iam_member" "mirth_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.mirth_sa.email}"
}

resource "google_project_iam_member" "mirth_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.mirth_sa.email}"
}

resource "google_project_iam_member" "mirth_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.mirth_sa.email}"
}

resource "google_project_iam_member" "mirth_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.mirth_sa.email}"
}

resource "google_storage_bucket_iam_member" "mirth_bucket_access" {
  bucket = google_storage_bucket.mirth_attachments.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.mirth_sa.email}"
}

# -----------------------------------------------------------------------------
# Cloud Monitoring - Alert Policies
# -----------------------------------------------------------------------------
resource "google_monitoring_alert_policy" "mirth_sync_failures" {
  display_name = "IHEP Mirth Connect - Sync Failures (${var.environment})"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "High error rate on EHR sync"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ihep-mirth-connect-${var.environment}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      duration        = "300s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = var.alert_notification_channels

  alert_strategy {
    auto_close = "1800s"
  }

  user_labels = merge(var.labels, {
    service  = "mirth-connect"
    severity = "critical"
  })
}

resource "google_monitoring_alert_policy" "mirth_high_latency" {
  display_name = "IHEP Mirth Connect - High Latency (${var.environment})"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Request latency > 5s"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"ihep-mirth-connect-${var.environment}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5000
      duration        = "300s"

      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  notification_channels = var.alert_notification_channels

  user_labels = merge(var.labels, {
    service  = "mirth-connect"
    severity = "warning"
  })
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------
output "mirth_connect_url" {
  value       = google_cloud_run_v2_service.mirth_connect.uri
  description = "Mirth Connect Cloud Run URL"
}

output "ehr_gateway_url" {
  value       = google_cloud_run_v2_service.ehr_integration_gateway.uri
  description = "EHR Integration Gateway Cloud Run URL"
}

output "mirth_db_connection" {
  value       = google_sql_database_instance.mirth_db.connection_name
  description = "Cloud SQL connection name for Mirth Connect"
  sensitive   = true
}

output "pubsub_inbound_topic" {
  value = google_pubsub_topic.ehr_inbound.name
}

output "pubsub_outbound_topic" {
  value = google_pubsub_topic.ehr_outbound.name
}
