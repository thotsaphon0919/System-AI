# Dockerfile for INFINI system_ai — deploys as a container image.
#
# Why this exists: Render's git-based deploy clones this repo from GitHub,
# which pulls Git LFS objects and is blocked whenever the GitHub account's
# monthly LFS bandwidth quota is exhausted. Building and pushing a Docker
# image instead means Render pulls layers from a container registry
# (Docker Hub / GHCR), never touching GitHub or Git LFS at deploy time.
#
# Build & push from your machine (see DEPLOY_WITH_DOCKER.md for full steps):
#   docker build -t YOUR_DOCKERHUB_USERNAME/infini-system-ai:latest .
#   docker push YOUR_DOCKERHUB_USERNAME/infini-system-ai:latest
#
# Then point the Render service at that image (Dashboard: New > Web Service
# > Existing Image, or `render services create --image ...`).

FROM python:3.11.9-slim

WORKDIR /app

# System deps: Pillow needs a couple of image libs to build/run cleanly.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so this layer is cached across rebuilds
# unless requirements.txt actually changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app. .dockerignore (see next to this file) keeps
# uploads/media out of the image the same way .gitignore keeps them out
# of git — they're restored from Cloudinary/Neon at runtime instead.
COPY . .

# Render sets $PORT at runtime and routes external traffic to it.
# start.py already reads $PORT for the proxy's public-facing port.
EXPOSE 10000

CMD ["python", "start.py"]
