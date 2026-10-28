FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/app
COPY pyproject.toml README.md ./
COPY app ./app
COPY data ./data
COPY dashboard.py ./dashboard.py
COPY scripts ./scripts
RUN pip install --no-cache-dir .
EXPOSE 8000 8501
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
