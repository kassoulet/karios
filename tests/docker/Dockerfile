# Dockerfile for testing KARIOS QGIS Plugin
# Usage: docker build -t karios-qgis-test .

FROM qgis/qgis:release-3_34

LABEL maintainer="KARIOS QGIS Plugin"
LABEL description="QGIS with KARIOS plugin for dependency checker testing"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    python3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy plugin files
COPY . /workspace/karios-qgis/

# Install KARIOS library from submodule (if present)
RUN if [ -d "/workspace/karios-qgis/karios" ]; then \
        cd /workspace/karios-qgis/karios && \
        pip3 install --no-cache-dir -e . || true; \
    fi

# Compile Qt resources
RUN cd /workspace/karios-qgis && \
    if command -v pyrcc6 &> /dev/null; then \
        pyrcc6 -o resources/resources.py resources/resources.qrc; \
    elif command -v pyrcc5 &> /dev/null; then \
        pyrcc5 -o resources/resources.py resources/resources.qrc; \
    else \
        echo "Warning: No pyrcc found, resources.py may already exist"; \
    fi

# Install plugin to QGIS plugins directory
RUN mkdir -p /root/.local/share/QGIS/QGIS3/profiles/default/python/plugins && \
    cp -r /workspace/karios-qgis /root/.local/share/QGIS/QGIS3/profiles/default/python/plugins/karios_qgis

# Copy test script
COPY tests/docker/test_plugin.py /workspace/test_plugin.py

# Default command runs the test
CMD ["python3", "/workspace/test_plugin.py"]
