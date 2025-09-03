# Firestore OpenTofu Setup

## Prerequisites
- Google Cloud SDK installed
- OpenTofu installed
- Authenticated with Google Cloud: `gcloud auth application-default login`

## Usage

1. Initialize and apply:
   ```bash
   tofu init
   tofu plan
   tofu apply
   ```

## What this creates
- A cloud storage bucket which stores the remote state (a bit inception sorry)
- Enables Firestore and App Engine APIs
- Creates App Engine application
- Sets up Firestore database in native mode