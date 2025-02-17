FROM python:3.11-slim AS build
WORKDIR /app
RUN python -m venv /venv && /venv/bin/pip install --no-cache-dir --upgrade fastapi uvicorn

FROM python:3.11-slim AS final
WORKDIR /app
COPY --from=build /venv /venv
COPY main.py main.py
COPY src src
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH=/app
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
