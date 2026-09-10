FROM postgres:16-alpine

# Optional: Environment variables can also be set here, 
# but keeping them in docker-compose.yml or a .env file is recommended.
ENV POSTGRES_DB=default_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

EXPOSE 5432