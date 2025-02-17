FROM python:3.11-slim AS build
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir poetry
COPY pyproject.toml /app/
RUN poetry config virtualenvs.create true && poetry install --no-interaction --no-ansi --only main

FROM python:3.11-slim AS final
WORKDIR /app
COPY --from=build /root/.cache/pypoetry/virtualenvs/*/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . /app/bet_maker/
WORKDIR /app/bet_maker/
RUN chmod +x entrypoint.sh
EXPOSE 8081
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
ENTRYPOINT ["./entrypoint.sh"]
