# script to create docker container for the Deltares JupyterHub IDP environment

# Start from a base Jupyter image
FROM jupyter/scipy-notebook:latest

# Switch to root to install system packages
USER root

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    vim \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to the notebook user
USER $NB_UID

# Install Python packages
RUN pip install --no-cache-dir \
    pandas==2.0.0 \
    scikit-learn==1.3.0 \
    plotly==5.14.0 \
    seaborn==0.12.0

# Install additional conda packages (optional)
RUN conda install -c conda-forge \
    xgboost \
    lightgbm \
    && conda clean -afy

# Set working directory
WORKDIR /home/jovyan/work

# Copy any startup scripts or configurations (optional)
# COPY startup.sh /usr/local/bin/
# RUN chmod +x /usr/local/bin/startup.sh