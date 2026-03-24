FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src:/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir pip -U \
    && pip install --no-cache-dir -e .

RUN python -c "import nltk; nltk.download('punkt', quiet=True)"

EXPOSE 8000

CMD ["uvicorn", "research_llm.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
