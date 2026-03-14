FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/app.py
COPY .streamlit /app/.streamlit

EXPOSE 8080

CMD ["/bin/sh", "-c", "streamlit run /app/app.py"]
