# Videoflix Backend
 
A Django REST API backend for the Videoflix streaming platform. Supports user authentication with JWT via HttpOnly cookies, HLS video streaming, background video processing with Django-RQ, and Redis caching.
 
---
 
## Tech Stack
 
- **Django** – Web framework
- **Django REST Framework** – REST API
- **PostgreSQL** – Primary database
- **Redis** – Caching and message broker
- **Django-RQ** – Background job processing
- **FFMPEG** – Video conversion to HLS (480p, 720p, 1080p)
- **Docker** – Containerized deployment
- **Gunicorn** – Production WSGI server
- **Whitenoise** – Static file serving
 
---
 
## Features
 
- User registration with email confirmation
- JWT authentication via HttpOnly cookies
- Account activation via email link
- Password reset via email
- Video upload with automatic HLS conversion (480p, 720p, 1080p)
- Background video processing with Django-RQ
- Redis caching layer
- Django Admin for content management
- CORS support for frontend communication
 
---
 
## Prerequisites
 
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords) for email sending
 
---
 
## Setup & Installation
 
### 1. Clone the repository
 
```bash
git clone https://github.com/your-username/videoflix-backend.git
cd videoflix-backend
```
 
### 2. Create your `.env` file
 
Copy the template and fill in your values:
 
```bash
cp .env.template .env
```
 
Open `.env` and configure the following:
 
```dotenv
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=your_secure_password
DJANGO_SUPERUSER_EMAIL=admin@example.com
 
SECRET_KEY="your_secret_django_key"
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
 
USE_POSTGRES=true
 
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=db
DB_PORT=5432
 
REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0
 
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_google_app_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=your_email@gmail.com
 
FRONTEND_URL=http://127.0.0.1:5500
```
 
### 3. Start with Docker
 
```bash
docker compose up --build
```
 
Docker will automatically:
- Wait for PostgreSQL to be ready
- Run all migrations
- Collect static files
- Create the superuser
- Start the RQ worker for background jobs
- Start Gunicorn on port 8000
 
### 4. Access the application
 
| Service | URL |
|---|---|
| API | http://localhost:8000/api/ |
| Django Admin | http://localhost:8000/admin/ |
 
---
 
## Project Structure
 
```
videoflix-backend/
├── core/                   # Django project settings and URLs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/                  # User authentication app
│   ├── api/
│   │   ├── views.py        # Auth endpoints
│   │   ├── serializers.py  # Request/response validation
│   │   └── urls.py         # Auth URL routes
│   ├── templates/
│   │   └── emails/         # HTML email templates
│   ├── models.py           # CustomUser model
│   ├── admin.py            # Admin configuration
│   └── utils.py            # JWT auth, email helpers
├── videos/                 # Video management app
│   ├── api/
│   │   ├── views.py        # Video endpoints
│   │   ├── serializers.py  # Request/response validation
│   │   └── urls.py         # Video URL routes
│   ├── models.py           # Video and Genre models
│   ├── admin.py            # Admin configuration
│   ├── signals.py          # Auto-trigger HLS conversion
│   └── utils.py            # FFMPEG conversion helpers
├── backend.Dockerfile      # Docker image definition
├── backend.entrypoint.sh   # Docker startup script
├── docker-compose.yml      # Docker services configuration
├── requirements.txt        # Python dependencies
└── .env.template           # Environment variables template
```
 
---
 
## API Endpoints
 
### Authentication
 
| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| POST | `/api/register/` | Register a new user | No |
| GET | `/api/activate/<uid>/<token>/` | Activate account via email link | No |
| POST | `/api/login/` | Login and receive JWT cookies | No |
| POST | `/api/logout/` | Logout and blacklist refresh token | Yes |
| POST | `/api/password_reset/` | Request password reset email | No |
| POST | `/api/password_confirm/<uid>/<token>/` | Confirm new password | No |
 
### Videos
 
| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| GET | `/api/video/` | List all videos | Yes |
| GET | `/api/video/<id>/<resolution>/index.m3u8` | Get HLS manifest | Yes |
| GET | `/api/video/<id>/<resolution>/<segment>/` | Get HLS segment | Yes |
 
---
 
## Local Development (without Docker)
 
For local development, update your `.env`:
 
```dotenv
USE_POSTGRES=false
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
 
Then run:
 
```bash
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
 
Emails will appear in the terminal instead of being sent.
 
---
 
## Adding Videos
 
Videos can only be added via the Django Admin panel:
 
1. Go to http://localhost:8000/admin/
2. Login with your superuser credentials
3. Navigate to **Videos → Add Video**
4. Fill in title, description, genre and upload a video file
5. Save – FFMPEG will automatically convert the video to 480p, 720p and 1080p in the background
 
---
 
## Environment Variables
 
| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | `your-secret-key` |
| `DEBUG` | Debug mode | `True` / `False` |
| `USE_POSTGRES` | Use PostgreSQL instead of SQLite | `true` / `false` |
| `DB_NAME` | PostgreSQL database name | `videoflix_db` |
| `DB_USER` | PostgreSQL user | `videoflix_user` |
| `DB_PASSWORD` | PostgreSQL password | `supersecret` |
| `DB_HOST` | PostgreSQL host | `db` |
| `REDIS_HOST` | Redis host | `redis` |
| `REDIS_LOCATION` | Redis connection URL | `redis://redis:6379/1` |
| `EMAIL_BACKEND` | Email backend | `smtp` or `console` |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_HOST_USER` | SMTP email address | `you@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Gmail App Password | `xxxx xxxx xxxx xxxx` |
| `FRONTEND_URL` | Frontend base URL for email links | `http://127.0.0.1:5500` |
 
---
 
## Stopping Docker
 
```bash
docker compose down
```
 
To also remove all data (database, media files):
 
```bash
docker compose down -v
```
 
---
 
## Frontend
 
The frontend repository can be found here:
[https://github.com/Developer-Akademie-Backendkurs/project.Videoflix](https://github.com/Developer-Akademie-Backendkurs/project.Videoflix)
 
Start the frontend by opening `index.html` with **Live Server** in VS Code.
