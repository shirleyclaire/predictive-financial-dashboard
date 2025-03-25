FROM python:3.9-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /app/wheels /wheels
COPY . .

RUN pip install --no-cache /wheels/* && \
    rm -rf /wheels && \
    adduser --system --no-create-home appuser

USER appuser
EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
