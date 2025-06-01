# Stage 1: Build stage
FROM jupyter/base-notebook:latest AS builder

USER root

# Setup initial python environment
RUN python3 -m pip install uvicorn fastapi fastapi-cli loguru pydantic ray[serve] -U -q

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        openjdk-11-jdk \
        nodejs \
        npm \
        jupyter \
        unzip \
        && rm -rf /var/lib/apt/lists/* \
    && npm install -g --unsafe-perm ijavascript \
    && ijsinstall --install=global

# Setup IJava kernel
RUN wget https://github.com/SpencerPark/IJava/releases/download/v1.3.0/ijava-1.3.0.zip \
    && unzip ijava-1.3.0.zip \
    && rm ijava-1.3.0.zip \
    && python3 install.py

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir -U \
    matplotlib \
    numpy \
    scipy \
    pandas \
    joblib \
    seaborn \
    scikit-learn \
    boto3 \
    awscli \
    bash_kernel \
    fastapi-mcp \
    && python -m bash_kernel.install

# Install python kernel with conda
RUN conda create -n python -q -y \
    -c plotly -c conda-forge -c defaults \
    python=3.11 \
    pip \
    numpy \
    scipy \
    pandas \
    tqdm \
    joblib \
    plotly \
    matplotlib \
    seaborn \
    networkx \
    && conda run -n python pip install --no-cache-dir ipykernel \
    && conda run -n python python -m ipykernel install --name python --display-name "Base Python environment with pip, numpy, scipy, pandas, tqdm, joblib, plotly, matplotlib, seaborn, and networkx" \
    && conda clean -afy

# Install scientific python kernel with conda
RUN conda create -n python_scientific -q -y \
    -c plotly -c conda-forge -c defaults \
    python=3.11 \
    pip \
    numpy \
    scipy \
    pandas \
    tqdm \
    joblib \
    scikit-learn \
    plotly \
    matplotlib \
    seaborn \
    && conda run -n python_scientific pip install --no-cache-dir ipykernel rdkit \
    && conda run -n python_scientific python -m ipykernel install --name python_scientific --display-name "Scientific Python with RDKit, scikit-learn, pip, numpy, scipy, pandas, tqdm, joblib, plotly, matplotlib, seaborn, and networkx" \
    && conda clean -afy

# Create and configure jovyan user
RUN mkdir -p /home/jovyan/.python && chown -R jovyan /home/jovyan

# Stage 2: Runtime stage
FROM jupyter/base-notebook:latest

USER root
WORKDIR /files
RUN chmod 777 -R /files

# Copy installed kernels and dependencies from builder
COPY --from=builder /opt/conda /opt/conda
COPY --from=builder /usr/local/share/jupyter /usr/local/share/jupyter
COPY --from=builder /home/jovyan/.local /home/jovyan/.local
COPY --from=builder /home/jovyan/.python /home/jovyan/.python

# Set ownership
RUN chown -R jovyan:users /home/jovyan

USER jovyan

# Configure environment
WORKDIR /code_repo_location/app
COPY ./app/ .

# Set environment variables
ENV MPLCONFIGDIR=/tmp \
    PYDEVD_DISABLE_FILE_VALIDATION=1 \
    RAY_memory_monitor_refresh_ms=50 \
    RAY_memory_usage_threshold=0.90 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    JOBLIB_MULTIPROCESSING=0

EXPOSE 8080

# Health check
HEALTHCHECK --interval=5s --timeout=60s --start-period=5s --retries=3 \
    CMD python /code_repo_location/app/healthcheck.py || exit 1

LABEL "autoheal"="true"

#ENTRYPOINT ["python", "/code_repo_location/app/main_ray.py"]
ENTRYPOINT ["python", "/code_repo_location/app/main.py"]