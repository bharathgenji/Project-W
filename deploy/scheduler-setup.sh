#!/usr/bin/env bash
########################################################################
# Cloud Scheduler Setup for Construction Lead Generation MVP
#
# Creates three Cloud Scheduler jobs that trigger the ingestion and
# scraping services on a daily schedule via authenticated HTTP POST.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Cloud Scheduler API enabled
#   - Cloud Run services already deployed
#   - Service account with roles/run.invoker permission
#
# Usage:
#   ./deploy/scheduler-setup.sh <PROJECT_ID> <REGION> <SERVICE_ACCOUNT_EMAIL>
#
# Example:
#   ./deploy/scheduler-setup.sh my-project us-central1 scheduler-sa@my-project.iam.gserviceaccount.com
########################################################################

set -euo pipefail

# ---- Parse arguments ----

if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <PROJECT_ID> <REGION> <SERVICE_ACCOUNT_EMAIL>"
    echo ""
    echo "Arguments:"
    echo "  PROJECT_ID             GCP project ID"
    echo "  REGION                 GCP region (e.g., us-central1)"
    echo "  SERVICE_ACCOUNT_EMAIL  Service account email for invoking Cloud Run"
    echo ""
    echo "Example:"
    echo "  $0 my-leadgen-project us-central1 scheduler-sa@my-leadgen-project.iam.gserviceaccount.com"
    exit 1
fi

PROJECT_ID="$1"
REGION="$2"
SERVICE_ACCOUNT_EMAIL="$3"
TIMEZONE="America/Chicago"

echo "============================================"
echo "Cloud Scheduler Setup"
echo "============================================"
echo "Project:         ${PROJECT_ID}"
echo "Region:          ${REGION}"
echo "Service Account: ${SERVICE_ACCOUNT_EMAIL}"
echo "Timezone:        ${TIMEZONE}"
echo "============================================"
echo ""

# ---- Ensure Cloud Scheduler API is enabled ----

echo "Ensuring Cloud Scheduler API is enabled..."
gcloud services enable cloudscheduler.googleapis.com \
    --project="${PROJECT_ID}" \
    --quiet

# ---- Helper function ----

get_service_url() {
    local service_name="$1"
    local url
    url=$(gcloud run services describe "${service_name}" \
        --region="${REGION}" \
        --project="${PROJECT_ID}" \
        --format="value(status.url)" 2>/dev/null)
    if [[ -z "${url}" ]]; then
        echo "ERROR: Could not retrieve URL for Cloud Run service '${service_name}'." >&2
        echo "       Make sure the service is deployed in region '${REGION}'." >&2
        exit 1
    fi
    echo "${url}"
}

create_or_update_job() {
    local job_name="$1"
    local schedule="$2"
    local url="$3"
    local description="$4"

    echo "Setting up scheduler job: ${job_name}"
    echo "  Schedule:    ${schedule} (${TIMEZONE})"
    echo "  Target URL:  ${url}"
    echo "  Description: ${description}"

    # Check if job already exists
    if gcloud scheduler jobs describe "${job_name}" \
        --location="${REGION}" \
        --project="${PROJECT_ID}" \
        > /dev/null 2>&1; then

        echo "  Job exists, updating..."
        gcloud scheduler jobs update http "${job_name}" \
            --location="${REGION}" \
            --project="${PROJECT_ID}" \
            --schedule="${schedule}" \
            --time-zone="${TIMEZONE}" \
            --uri="${url}" \
            --http-method=POST \
            --oidc-service-account-email="${SERVICE_ACCOUNT_EMAIL}" \
            --oidc-token-audience="${url}" \
            --headers="Content-Type=application/json" \
            --message-body='{}' \
            --description="${description}" \
            --attempt-deadline=600s \
            --max-retry-attempts=3 \
            --min-backoff=30s \
            --max-backoff=300s \
            --quiet
        echo "  Updated successfully."
    else
        echo "  Creating new job..."
        gcloud scheduler jobs create http "${job_name}" \
            --location="${REGION}" \
            --project="${PROJECT_ID}" \
            --schedule="${schedule}" \
            --time-zone="${TIMEZONE}" \
            --uri="${url}" \
            --http-method=POST \
            --oidc-service-account-email="${SERVICE_ACCOUNT_EMAIL}" \
            --oidc-token-audience="${url}" \
            --headers="Content-Type=application/json" \
            --message-body='{}' \
            --description="${description}" \
            --attempt-deadline=600s \
            --max-retry-attempts=3 \
            --min-backoff=30s \
            --max-backoff=300s \
            --quiet
        echo "  Created successfully."
    fi
    echo ""
}

# ---- Retrieve Cloud Run service URLs ----

echo "Retrieving Cloud Run service URLs..."
echo ""

PERMIT_INGESTER_URL=$(get_service_url "permit-ingester")
BID_INGESTER_URL=$(get_service_url "bid-ingester")
LICENSE_SCRAPER_URL=$(get_service_url "license-scraper")

echo "  permit-ingester: ${PERMIT_INGESTER_URL}"
echo "  bid-ingester:    ${BID_INGESTER_URL}"
echo "  license-scraper: ${LICENSE_SCRAPER_URL}"
echo ""

# ---- Create/Update Scheduler Jobs ----

# Job 1: Daily permit ingestion at 5:00 AM Central Time
create_or_update_job \
    "daily-permits" \
    "0 5 * * *" \
    "${PERMIT_INGESTER_URL}/ingest" \
    "Daily construction permit ingestion - runs at 5:00 AM CT"

# Job 2: Daily bid ingestion at 6:00 AM Central Time
create_or_update_job \
    "daily-bids" \
    "0 6 * * *" \
    "${BID_INGESTER_URL}/ingest" \
    "Daily government bid ingestion - runs at 6:00 AM CT"

# Job 3: Daily license scraping at 2:00 AM Central Time
create_or_update_job \
    "daily-scrape" \
    "0 2 * * *" \
    "${LICENSE_SCRAPER_URL}/scrape" \
    "Daily contractor license scraping - runs at 2:00 AM CT"

# ---- Summary ----

echo "============================================"
echo "Cloud Scheduler Setup Complete"
echo "============================================"
echo ""
echo "Jobs created/updated:"
echo ""

gcloud scheduler jobs list \
    --location="${REGION}" \
    --project="${PROJECT_ID}" \
    --filter="name:(daily-permits OR daily-bids OR daily-scrape)" \
    --format="table(name,schedule,state,httpTarget.uri)"

echo ""
echo "To manually trigger a job:"
echo "  gcloud scheduler jobs run daily-permits --location=${REGION} --project=${PROJECT_ID}"
echo "  gcloud scheduler jobs run daily-bids    --location=${REGION} --project=${PROJECT_ID}"
echo "  gcloud scheduler jobs run daily-scrape  --location=${REGION} --project=${PROJECT_ID}"
echo ""
echo "To pause a job:"
echo "  gcloud scheduler jobs pause <job-name> --location=${REGION} --project=${PROJECT_ID}"
echo ""
