FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system nova && adduser --system --ingroup nova nova
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x /app/entrypoint.sh && mkdir -p /app/media /app/staticfiles && chown -R nova:nova /app

USER nova
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
