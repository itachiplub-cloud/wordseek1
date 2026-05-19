FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m nltk.downloader words
RUN python -m nltk.downloader wordnet

COPY . .

CMD ["python", "seek2.py"]
