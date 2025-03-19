# Configure local SQLite database for testing purposes

 Set `DATABASE_URL` in the `.env` file to:

```bash
sqlite+aiosqlite:///.data/test.db
```

# Build docker image and run container

```bash
docker build . -t bet_maker_image:latest
docker run -p 8081:8081 --name bet_maker_container bet_maker_image:latest
```

Generate first migration:

```bash
alembic revision --autogenerate -m "Create bet table"
```

Apply migrations:

```bash
alembic upgrade head
```
