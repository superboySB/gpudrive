# Base image with CUDA and cuDNN support                                                                                      
FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

# 如果需要走代理
ENV http_proxy=http://127.0.0.1:8889
ENV https_proxy=http://127.0.0.1:8889

# Install essential packages
RUN apt-get update && apt-get install -y -q --no-install-recommends \
	software-properties-common \
        build-essential \
        cmake \
        git \
        curl \
        vim \
        gedit \
        ca-certificates \
        libjpeg-dev \
        libpng-dev \
        wget \
        libx11-dev \
        libxrandr-dev \
        libxinerama-dev \
        libxcursor-dev \
        libxi-dev \
        mesa-common-dev \
        libc++1 \
        openssh-client \
        ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/bin" sh

# Copy the gpudrive repository
COPY . /workspace/gpudrive
WORKDIR /workspace/gpudrive
RUN git submodule update --init --recursive

# Install python part using uv
RUN uv sync --frozen

# Install ipykernel for Jupyter support
RUN uv add ipykernel 
# && uv add "pufferlib@git+https://github.com/PufferAI/PufferLib.git@gpudrive"

# 设置 MADRONA_MWGPU_KERNEL_CACHE 环境变量，避免每次都重新编译 CUDA kernel
ENV MADRONA_MWGPU_KERNEL_CACHE=./gpudrive_cache

RUN mkdir build
WORKDIR /workspace/gpudrive/build
RUN uv run cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 && \
    find external -type f -name "*.tar" -delete
RUN ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1
RUN LD_LIBRARY_PATH=/usr/local/cuda/lib64/stubs/:$LD_LIBRARY_PATH uv run make -j
RUN rm /usr/local/cuda/lib64/stubs/libcuda.so.1
WORKDIR /workspace/gpudrive

# 映射 .venv/bin/python 到 python 和 python3，方便直接调用
RUN ln -sf /workspace/gpudrive/.venv/bin/python /usr/local/bin/python \
    && ln -sf /workspace/gpudrive/.venv/bin/python /usr/local/bin/python3

# 设置PYTHONPATH，让Python能够找到编译好的包和虚拟环境的site-packages
ENV PYTHONPATH=/workspace/gpudrive/build:/workspace/gpudrive/.venv/lib/python3.11/site-packages:$PYTHONPATH

# 设置虚拟环境变量，确保Python知道它运行在虚拟环境中
ENV VIRTUAL_ENV=/workspace/gpudrive/.venv
ENV PATH=/workspace/gpudrive/.venv/bin:$PATH

# 如需清理代理，取消注释
# ENV http_proxy=
# ENV https_proxy=
# ENV no_proxy=
# RUN rm -rf /var/lib/apt/lists/* && apt-get clean

CMD ["/bin/bash"]
LABEL org.opencontainers.image.source=https://github.com/Emerge-Lab/gpudrive
