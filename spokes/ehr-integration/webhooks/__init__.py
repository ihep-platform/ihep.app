"""
EHR Webhook Handlers

Processes incoming webhook events from EHR systems, validates signatures,
routes events by type, and publishes to GCP Pub/Sub for async processing.
"""
