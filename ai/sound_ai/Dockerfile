# HF Space Docker runtime
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# System deps: ffmpeg (4.4 in 22.04), Python 3.10, git, FFmpeg dev headers, and build tools for PyAV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg pkg-config \
      libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev \
      libavfilter-dev libswscale-dev libswresample-dev \
      build-essential python3.10 python3.10-distutils python3-dev python3-pip \
      git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Ensure python and pip
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    python -m pip install --upgrade pip

# Install PyTorch CUDA 12.1 wheels first to ensure GPU-enabled build
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0

# Then the rest of requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# App
COPY app.py /workspace/app.py
WORKDIR /workspace

# Expose for HF Spaces (Gradio)
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
