# CC6 Race Series App

A Flask web application for managing participants, races, and results. Built for Google Cloud Platform with Firestore database and OAuth authentication.

## Features

- **Participant Management**: Register and manage participants with Parkrun barcode tracking
- **Club Administration**: Manage running clubs and their short names/aliases
- **Season & Race Management**: Organise races by seasons with configurable age categories
- **Results Processing**: Upload and manage race results via CSV or manual entry
- **Public Results**: Public-facing results display for race participants
- **Admin Authentication**: Google OAuth-based admin access control
- **Bulk Operations**: CSV upload for participants and race results

## Architecture

- **Frontend**: Flask with Jinja2 templates
- **Backend**: Python Flask application
- **Database**: Google Firestore (NoSQL)
- **Authentication**: Google OAuth 2.0
- **Infrastructure**: Google Cloud Run (containerized deployment)
- **Secrets**: Google Secret Manager
- **Infrastructure as Code**: OpenTofu/Terraform

## Project Structure

```
cc6-app/
├── app/                    # Flask application
│   ├── templates/          # HTML templates
│   ├── static/            # CSS, images, robots.txt
│   ├── app.py             # Main Flask application
│   ├── api.py             # API blueprint (JSON endpoints)
│   ├── auth.py            # OAuth authentication
│   ├── database.py        # Firestore database operations
│   ├── Dockerfile         # Container configuration
│   └── test_*.py          # Test files
├── tofu/                  # Infrastructure as code
└── datastructure.md       # Firestore data model documentation
```

## Quick Start

### Prerequisites

- Google Cloud Project with billing enabled
- OpenTofu installed
- Docker (for local development)
- Python 3.14 (for local development)

### Deployment

1. **Configure infrastructure**:
   ```bash
   cd tofu
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your project details
   ```

2. **Deploy infrastructure**:
   ```bash
   tofu init
   tofu plan
   tofu apply
   ```

3. **Configure OAuth secrets**:
   - Create Google OAuth credentials in Google Cloud Console
   - Store client ID and secret in Secret Manager:
   ```bash
   gcloud secrets versions add oauth-client-id --data="your-client-id"
   gcloud secrets versions add oauth-client-secret --data="your-client-secret"
   ```

4. **Access the application**:
   - The application will be deployed to Cloud Run
   - Custom domain mapping available at `app.cc6.co.uk`

### Local Development

1. **Set up environment**:
   ```bash
   cd app
   pip install pipenv
   pipenv install --dev
   pipenv shell
   ```

2. **Configure environment variables**:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export FLASK_SECRET_KEY="your-secret-key"
   export GOOGLE_CLIENT_ID="your-oauth-client-id"
   export GOOGLE_CLIENT_SECRET="your-oauth-client-secret"
   ```

3. **Run locally**:
   ```bash
   python app.py
   ```

4. **Run tests**:
   ```bash
   make test
   ```

## Configuration

### Environment Variables

- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `FLASK_SECRET_KEY`: Flask session secret key
- `GOOGLE_CLIENT_ID`: OAuth client ID
- `GOOGLE_CLIENT_SECRET`: OAuth client secret
- `PORT`: Application port (default: 8080)

### Terraform Variables

- `project_id`: Google Cloud Project ID
- `region`: Deployment region (default: us-central1)
- `domain`: Custom domain for the application

## Data Model

The application uses Firestore with the following collections:

- **participants**: Runner registration data with parkrun barcode IDs
- **clubs**: Running club information and aliases
- **seasons**: Race seasons with configurable age categories
- **races**: Individual races within seasons
- **results**: Race results linked to participants
- **admin_emails**: Authorized administrator email addresses

See [datastructure.md](datastructure.md) for detailed schema documentation.

## API Endpoints

### Public Endpoints
- `GET /` - Home page
- `GET /results` - Public results display
- `GET /api/clubs` - List all clubs
- `GET /api/seasons` - List all seasons
- `GET /api/seasons/<season>` - Season details with races
- `GET /api/races/<season>/<race>` - Race results
- `GET /api/championship/<season>/<gender>` - Team championship standings
- `GET /api/individual-championship/<season>/<gender>` - Individual championship standings

### Admin Endpoints (OAuth required)
- `GET /participants` - Participant management
- `GET /clubs` - Club management
- `GET /seasons` - Season management
- `GET /races` - Race management
- `GET /api/participants` - Get participants data (JSON)
- `POST /upload_participants` - Bulk participant upload
- `POST /process_upload_results` - Bulk results upload

## Security

- Google OAuth 2.0 authentication for admin access
- Email-based authorization (configurable admin list)
- Secrets stored in Google Secret Manager
- HTTPS enforced in production
- Input validation and sanitization

## Monitoring & Logging

- Cloud Run automatic logging
- Application logs available in Google Cloud Logging
- Health checks via Cloud Run

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Run the test suite: `make test`
5. Submit a pull request

## License

This project is licensed under the MIT License.
