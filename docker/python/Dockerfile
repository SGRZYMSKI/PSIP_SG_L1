FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-dev \
        gcc \
        g++ \
        gdal-bin \
        python3-gdal \
        libgdal-dev \
        proj-bin \
        libproj-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --break-system-packages \
    geopandas \
    h3 \
    shapely

WORKDIR /app