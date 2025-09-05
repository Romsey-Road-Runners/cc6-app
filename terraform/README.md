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
- Deploys the CC6 API app
- Creates storage bucket for app source code

## App Deployment
The OpenTofu configuration will:
1. Package your app code into a zip file
2. Upload it to Google Cloud Storage
3. Deploy it to App Engine
4. Output the app URL