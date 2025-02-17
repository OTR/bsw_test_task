```bash
docker build . -t bet_maker_image:latest
docker run -p 8081:8081 --name bet_maker_container bet_maker_image:latest
```

Apply the first migration:

```bash
alembic revision --autogenerate -m "Create bet table"
```