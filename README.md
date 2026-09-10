# Gigger Python Backend

Gigger Backend is a Python-based REST API built with **FastAPI**. It provides the backend services and API endpoints used by the Gigger platform.

## Project Information

| Item                 | Information           |
| -------------------- | --------------------- |
| Project              | Gigger Python Backend |
| Language             | Python                |
| Framework            | FastAPI               |
| Database             | PostgreSQL            |
| Database Environment | Docker                |
| API Documentation    | `/gigger/docs`        |

## Technologies

* Python
* FastAPI
* PostgreSQL
* Docker
* SQLAlchemy
* Pydantic
* REST API

## Requirements

Before running the project, make sure the following are installed:

* Python 3.x
* Docker
* Docker Compose
* Git
* pip

Check Python:

```bash
python --version
```

Check Docker:

```bash
docker --version
```

Check Docker Compose:

```bash
docker compose version
```

## Project Setup

Clone the repository:

```bash
git clone <repository-url>
```

Enter the project directory:

```bash
cd gigger-python
```

## Python Virtual Environment

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment.

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## PostgreSQL Database

The project uses **PostgreSQL** as the database.

PostgreSQL runs inside a **Docker container** rather than being installed directly on the development machine.

Check running containers:

```bash
docker ps
```

Start the database containers:

```bash
docker compose up -d
```

Check container status:

```bash
docker compose ps
```

View database/container logs:

```bash
docker compose logs
```

Stop the containers:

```bash
docker compose down
```

To stop containers without removing the database volumes:

```bash
docker compose down
```

> Database configuration such as username, password, database name, port, and connection URL should be configured according to the project's Docker Compose configuration.

## Environment Configuration

The project may require environment variables for database and application configuration.

Typical configuration values include:

```text
DATABASE_URL
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
```

Do not commit passwords, database credentials, API keys, tokens, or other secrets to GitHub.

If an environment file is required, create it locally:

```text
.env
```

A safe example file can be provided as:

```text
.env.example
```

without real credentials.

## Run the FastAPI Application

After starting PostgreSQL and activating the Python virtual environment, start the FastAPI server.

A typical command is:

```bash
uvicorn main:app --reload
```

If the application uses a different entry point, use the project's configured FastAPI application module.

For example:

```bash
uvicorn app.main:app --reload
```

The `--reload` option automatically reloads the server when source code changes during development.

## API Documentation

FastAPI automatically provides interactive Swagger documentation.

Swagger UI:

```text
/gigger/docs
```

If the application is running locally on port `8000`, open:

```text
http://localhost:8000/gigger/docs
```

The Swagger documentation allows developers to:

* View available API endpoints
* View request parameters
* View request and response schemas
* Test API endpoints
* Check authentication requirements
* Review API responses

## API Documentation Endpoints

### Swagger UI

```text
/gigger/docs
```

### OpenAPI Schema

FastAPI also provides the OpenAPI specification through its configured OpenAPI endpoint.

The exact URL depends on the application's FastAPI configuration.

## Database

The application uses:

```text
PostgreSQL
```

PostgreSQL is managed through Docker.

Recommended development workflow:

```text
FastAPI Application
        │
        ▼
    REST APIs
        │
        ▼
   PostgreSQL
        │
        ▼
 Docker Container
```

## Docker

Start the development environment:

```bash
docker compose up -d
```

Check running services:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Stop the environment:

```bash
docker compose down
```

Rebuild containers:

```bash
docker compose up -d --build
```

## Development Workflow

Recommended development workflow:

```text
1. Pull the latest changes
2. Activate the Python virtual environment
3. Start PostgreSQL using Docker
4. Install/update Python dependencies
5. Start the FastAPI development server
6. Test APIs using Swagger
7. Make changes
8. Run tests
9. Commit changes
10. Push changes
```

Example:

```bash
git checkout develop
git pull

source venv/bin/activate

docker compose up -d

pip install -r requirements.txt

uvicorn main:app --reload
```

## Useful Commands

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Generate Requirements

If dependencies have been added:

```bash
pip freeze > requirements.txt
```

### Run FastAPI

```bash
uvicorn main:app --reload
```

### Run Docker

```bash
docker compose up -d
```

### Stop Docker

```bash
docker compose down
```

### Check Docker Containers

```bash
docker ps
```

### View Docker Logs

```bash
docker compose logs -f
```

## Git Branches

Recommended branches:

```text
main
develop
feature/<feature-name>
bugfix/<bug-name>
```

### Main

The `main` branch represents the production/customer-ready version.

### Develop

The `develop` branch is used for active development and testing.

### Feature

Feature branches should be created from `develop`.

Example:

```bash
git checkout develop
git checkout -b feature/user-profile
```

## Security

Never commit sensitive information to GitHub.

Do not commit:

```text
.env
*.pem
*.key
Passwords
Database passwords
API keys
Access tokens
Private keys
Service account credentials
```

Use `.env.example` to document required environment variables without including real credentials.

## Project Structure

The exact structure may vary depending on the current project implementation.

A typical FastAPI project structure is:

```text
gigger-python/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
│
├── tests/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Notes

* Backend framework: **FastAPI**
* Programming language: **Python**
* Database: **PostgreSQL**
* PostgreSQL runs using **Docker**
* Interactive API documentation is available at **`/gigger/docs`**
* Use Docker Compose to start the database environment.
* Do not commit sensitive credentials to the repository.
# gigger-python
# gigger-python
