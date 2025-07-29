FROM python:3.13-slim-bookworm

# Set working directory
WORKDIR /app

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y    --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/0.8.3/install.sh /uv-installer.sh


RUN sh /uv-installer.sh && rm /uv-installer.sh


# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Path to virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy project files and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --locked

EXPOSE 8000

# Copy the rest of the source code
COPY . .

CMD ["bash", "entrypoint.sh"]
