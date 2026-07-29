FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.10-slim
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# HuggingFace Spaces runs as user 1000
RUN useradd -m -u 1000 user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Fish Speech
RUN pip install --no-cache-dir git+https://github.com/fishaudio/fish-speech.git

# Copy source
COPY --chown=user backend/ backend/
COPY --chown=user data/ data/
COPY --from=frontend-builder --chown=user /frontend/dist frontend/dist

# Writable data dirs
RUN mkdir -p data/recordings data/output data/voices data/scripts && chown -R user:user data/

USER user

EXPOSE 7860

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
