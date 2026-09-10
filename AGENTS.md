# AGENTS.md

# Gigger Python Backend — Codex Instructions

## 1. Project Overview

This repository contains the Python backend for the Gigger platform.

The backend is a REST API built with FastAPI and uses PostgreSQL as its primary database.

### Technology Stack

```text
Python
FastAPI
PostgreSQL
Docker
Docker Compose
SQLAlchemy
Pydantic
REST API
```

The interactive API documentation is available at:

```text
/gigger/docs
```

When running locally on port `8000`:

```text
http://localhost:8000/gigger/docs
```

---

# 2. General Codex Rules

Before modifying the project:

1. Inspect the existing project structure.
2. Understand the existing implementation.
3. Search for existing functionality before creating new functionality.
4. Reuse existing services, utilities, models, schemas, and database patterns.
5. Follow the existing project architecture.
6. Keep changes focused on the requested task.
7. Do not modify unrelated files.
8. Do not introduce unnecessary dependencies.
9. Do not rewrite working code without a clear reason.
10. Do not change API contracts unless explicitly requested.
11. Do not change database structure without checking existing migrations and models.
12. Run appropriate validation after making changes.

The existing implementation is the source of truth.

Do not assume that a generic FastAPI architecture is being used if the repository already has its own architecture.

---

# 3. Python Environment

The project uses Python.

Create a virtual environment:

```bash
python -m venv venv
```

Activate on macOS/Linux:

```bash
source venv/bin/activate
```

Activate on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Do not globally install project dependencies when the virtual environment is available.

---

# 4. Dependencies

The main dependencies include:

```text
FastAPI
SQLAlchemy
Pydantic
PostgreSQL-related database driver(s)
```

Always inspect `requirements.txt` before adding or changing dependencies.

Before adding a new package:

1. Check whether the required functionality already exists.
2. Search the repository for an existing implementation.
3. Check whether an existing dependency can solve the problem.
4. Add a new dependency only when necessary.

Do not upgrade all dependencies as part of an unrelated task.

Do not change major dependency versions without checking compatibility.

After dependency changes:

```bash
pip install -r requirements.txt
```

---

# 5. FastAPI Application

The backend uses FastAPI.

Do not assume the application entry point is:

```text
main:app
```

Inspect the repository to determine the actual FastAPI entry point.

Possible examples include:

```bash
uvicorn main:app --reload
```

or:

```bash
uvicorn app.main:app --reload
```

Before changing application initialization, inspect the existing FastAPI application configuration.

Preserve existing:

* Middleware
* Routers
* Exception handlers
* Authentication
* CORS configuration
* Startup/shutdown logic
* Database initialization
* Application configuration

---

# 6. API Documentation

Swagger UI is configured under:

```text
/gigger/docs
```

Local URL:

```text
http://localhost:8000/gigger/docs
```

When adding or modifying an API endpoint:

1. Make sure the endpoint is registered with the correct router.
2. Use appropriate Pydantic schemas.
3. Define request parameters correctly.
4. Define response models where the existing architecture uses them.
5. Preserve authentication requirements.
6. Verify the endpoint through Swagger when practical.

Do not remove or change the `/gigger/docs` configuration unless explicitly requested.

---

# 7. API Design

Before creating a new endpoint:

1. Search for similar endpoints.
2. Check the existing router structure.
3. Check existing service functions.
4. Check existing database/repository functions.
5. Check existing Pydantic schemas.
6. Check existing authentication/authorization logic.

Follow the existing API naming conventions.

Maintain consistency for:

* HTTP methods
* URL paths
* Request schemas
* Response schemas
* Status codes
* Error responses
* Authentication
* Validation

Do not introduce a completely different API pattern for a single endpoint.

---

# 8. Database

The project uses:

```text
PostgreSQL
```

PostgreSQL runs inside Docker.

Do not assume PostgreSQL is installed directly on the developer's machine.

Start the database environment with:

```bash
docker compose up -d
```

Check containers:

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs -f
```

Stop containers:

```bash
docker compose down
```

---

# 9. Database Changes

Before changing database-related code:

1. Inspect existing SQLAlchemy models.
2. Inspect existing database connection code.
3. Inspect existing repositories/services.
4. Check whether the project uses migrations.
5. Follow the existing migration strategy.
6. Avoid destructive database changes unless explicitly requested.

Do not delete or rename database columns simply to make code changes easier.

Consider backward compatibility when modifying:

* Tables
* Columns
* Relationships
* Constraints
* Indexes
* Enums

If a schema change is required, clearly identify the migration or database update that is needed.

---

# 10. SQLAlchemy

The project uses SQLAlchemy.

Reuse the existing SQLAlchemy configuration and session management.

Before creating a new database session or engine:

1. Search the project for the existing database configuration.
2. Reuse the existing implementation.
3. Follow the current dependency-injection pattern.

Do not create multiple database engines unnecessarily.

Do not hard-code database credentials.

---

# 11. Pydantic

The project uses Pydantic for validation and data schemas.

Reuse existing schemas where possible.

When creating or modifying schemas:

* Use clear field names.
* Preserve existing API response formats.
* Add validation where appropriate.
* Avoid duplicating existing schemas.
* Consider backward compatibility.

Do not expose database-only fields through API responses unless they are intentionally part of the API contract.

---

# 12. Authentication and Authorization

Before modifying authentication:

1. Search the existing authentication implementation.
2. Identify how users are authenticated.
3. Identify how access tokens are handled.
4. Identify existing dependencies/middleware.
5. Check role and permission handling.
6. Reuse existing authorization mechanisms.

Do not introduce a second authentication system without an explicit requirement.

Do not bypass authentication or authorization for convenience.

Do not hard-code credentials or tokens.

---

# 13. Error Handling

Follow the existing error-handling pattern.

When handling API errors:

* Return appropriate HTTP status codes.
* Provide useful error responses.
* Avoid exposing internal stack traces to clients.
* Preserve existing exception handlers.
* Log errors appropriately when the existing project supports logging.

Do not silently swallow exceptions.

Do not use broad exception handling unless necessary.

For example, avoid unnecessarily replacing specific exceptions with:

```python
except Exception:
    pass
```

---

# 14. Environment Variables

Application configuration may use environment variables such as:

```text
DATABASE_URL
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
```

Inspect the existing configuration before adding new environment variables.

Never hard-code:

* Database passwords
* API keys
* Access tokens
* Private keys
* Service-account credentials
* Production credentials

Use `.env` locally when required.

Use `.env.example` to document required configuration without real secrets.

---

# 15. Secrets

This project must never contain committed secrets.

Never commit:

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
Cloud credentials
```

Before committing code, check for accidental credentials.

Do not print secrets in:

* Source code
* Logs
* Error messages
* Documentation
* Commit messages
* Terminal output
* Test fixtures

If a secret is discovered in Git history, do not simply ignore it.

Stop and notify the developer that the credential should be removed from history and rotated/revoked if it is real.

---

# 16. Google Cloud Credentials

The repository previously contained:

```text
lib/gigger-google-service.json
```

This file must not be committed if it contains Google Cloud service-account credentials.

Keep it excluded through `.gitignore`.

Do not recreate or commit this file.

If the application requires Google Cloud credentials locally, obtain them through the team's approved secure credential-management process.

Never place service-account private keys directly into source control.

---

# 17. Docker

The database environment uses Docker.

Common commands:

```bash
docker compose up -d
```

```bash
docker compose ps
```

```bash
docker compose logs -f
```

```bash
docker compose down
```

```bash
docker compose up -d --build
```

Before modifying Docker configuration:

1. Inspect the existing `docker-compose.yml`.
2. Inspect the `Dockerfile`.
3. Check environment variables.
4. Check mounted volumes.
5. Check exposed ports.
6. Check service dependencies.

Do not change ports or volumes without understanding their effect on the development environment.

---

# 18. API + Database Development Flow

The normal development architecture is:

```text
Client
  │
  ▼
FastAPI
  │
  ├── Routers
  │
  ├── Services
  │
  ├── Schemas
  │
  └── SQLAlchemy
          │
          ▼
     PostgreSQL
          │
          ▼
    Docker Container
```

When implementing backend functionality, follow the existing separation of responsibilities.

Avoid putting:

* Complex database queries directly in routers
* Business logic directly in API route functions
* Validation logic unnecessarily inside database models

Use the existing project architecture instead.

---

# 19. Project Structure

The exact structure of this repository is the source of truth.

Do not create a generic structure just because it is common in FastAPI projects.

A possible structure may look like:

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
├── AGENTS.md
└── README.md
```

Before creating files, inspect the actual repository structure and place files according to existing conventions.

---

# 20. Testing

Before completing a task, identify the appropriate tests.

If the repository contains tests, run the relevant tests.

Typical command:

```bash
pytest
```

For a specific test:

```bash
pytest path/to/test_file.py
```

Do not claim that tests passed unless they were actually executed.

If tests cannot be run, explain why.

When adding new functionality, add or update tests when the existing project testing strategy supports it.

---

# 21. Code Quality

Write maintainable Python code.

Prefer:

* Clear naming
* Type hints
* Small functions
* Reusable services
* Explicit error handling
* Existing project patterns
* Minimal duplication
* Proper validation

Avoid:

* Unnecessary abstractions
* Duplicate code
* Dead code
* Unused imports
* Debugging statements
* Hard-coded configuration
* Hard-coded credentials
* Large unrelated refactors

Remove temporary debugging code before completing the task.

---

# 22. Logging

Use the existing logging system if one exists.

Do not log:

* Passwords
* Access tokens
* Private keys
* Database credentials
* Authentication headers
* Sensitive user information

When debugging an issue, log useful contextual information without exposing secrets.

---

# 23. Git Workflow

Recommended branches:

```text
main
develop
feature/<feature-name>
bugfix/<bug-name>
```

`main` represents the production/customer-ready version.

`develop` is used for active development and testing.

Feature branches should normally be created from `develop`.

Example:

```bash
git checkout develop
git pull
git checkout -b feature/user-profile
```

Before committing:

```bash
git status
```

Review changed files before committing.

Do not commit generated files, local configuration, credentials, or secrets.

---

# 24. Git Safety

Do not perform these operations unless explicitly requested:

```text
git push --force
git reset --hard
git rebase
git filter-repo
Deleting branches
Rewriting shared history
Deleting database data
```

If a force push or history rewrite appears necessary, explain the reason before doing it.

Never rewrite Git history merely to hide a mistake.

---

# 25. Development Workflow

Recommended workflow:

```text
1. Pull the latest changes
2. Inspect the current project
3. Activate the Python virtual environment
4. Start PostgreSQL with Docker
5. Install dependencies
6. Understand the requested change
7. Search for existing implementations
8. Implement the smallest appropriate change
9. Run tests
10. Check for secrets
11. Review changed files
12. Commit changes
```

Typical setup:

```bash
git checkout develop
git pull

source venv/bin/activate

docker compose up -d

pip install -r requirements.txt

uvicorn <actual-entry-point> --reload
```

Do not assume the entry point without checking the repository.

---

# 26. Before Modifying Code

Always inspect relevant files first.

For example, when modifying an API endpoint:

```text
Router
  ↓
Schema
  ↓
Service
  ↓
Repository / Database
  ↓
Model
```

When modifying database behavior:

```text
Database configuration
  ↓
SQLAlchemy session
  ↓
Model
  ↓
Repository / Service
  ↓
API
```

When modifying authentication:

```text
Authentication configuration
  ↓
Token handling
  ↓
Auth dependency
  ↓
Route protection
  ↓
User/permission logic
```

Use the actual project architecture rather than assuming these exact layers exist.

---

# 27. API Changes

When changing an existing endpoint, consider:

```text
HTTP method
URL
Request parameters
Request body
Validation
Authentication
Authorization
Database behavior
Response schema
HTTP status codes
Error responses
Existing clients
```

Do not make breaking API changes without explicit approval.

If an API contract must change, clearly identify the affected endpoint and expected impact.

---

# 28. Database Compatibility

When modifying database functionality:

* Preserve existing data where possible.
* Avoid destructive migrations.
* Consider existing production data.
* Check relationships before changing models.
* Check constraints and indexes.
* Check existing migrations.
* Ensure application code and database schema remain compatible.

Never delete production data as part of a normal development task.

---

# 29. Do Not Invent Missing Configuration

If required information is missing, do not invent:

* Database credentials
* API URLs
* Production secrets
* Cloud credentials
* Authentication tokens
* External service IDs
* Firebase/Google credentials

Use placeholders where appropriate and clearly identify what configuration must be supplied by the developer.

---

# 30. Minimal Change Principle

For every task:

```text
Understand
    ↓
Search
    ↓
Reuse
    ↓
Modify minimally
    ↓
Validate
```

Do not turn a small bug fix into a full architectural refactor.

If a larger refactor is genuinely necessary, explain why before expanding the scope.

---

# 31. Final Validation

Before considering a task complete:

1. Run `git status`.
2. Review all modified files.
3. Check for accidental changes.
4. Check for secrets.
5. Run relevant tests.
6. Verify the API if applicable.
7. Verify database behavior if applicable.
8. Verify Docker services if applicable.
9. Confirm the requested functionality.
10. Report any validation that could not be completed.

Useful commands include:

```bash
git status
```

```bash
pytest
```

```bash
docker compose ps
```

```bash
docker compose logs -f
```

---

# 32. Final Response Format

When completing a coding task, provide a concise summary:

```text
Changes:
- <change 1>
- <change 2>

Validation:
- <test/check performed>
- <result>

Notes:
- <anything the developer needs to know>
```

Do not claim successful validation if the command was not actually run.

If there is a remaining issue, clearly state it.

---

# 33. Most Important Rules

The following rules have priority:

1. Never commit secrets.
2. Never expose credentials.
3. Do not invent missing configuration.
4. Preserve existing API contracts unless explicitly asked to change them.
5. Reuse the existing project architecture.
6. Do not introduce unnecessary dependencies.
7. Do not make unrelated changes.
8. Do not perform destructive database operations without explicit approval.
9. Do not force-push or rewrite shared Git history without explicit approval.
10. Always validate changes before reporting completion.

The existing Gigger Python Backend implementation is the source of truth.
