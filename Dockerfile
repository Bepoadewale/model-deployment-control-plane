FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY control-plane ./control-plane
RUN pip install --no-cache-dir .
COPY fixtures ./fixtures
COPY scripts ./scripts
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "modelcp.api:app", "--host", "0.0.0.0", "--port", "8080"]
