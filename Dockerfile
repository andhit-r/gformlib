# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tooling
RUN pip install --no-cache-dir build

COPY . .

# Build the wheel
RUN python -m build --wheel --outdir /dist

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="gformlib"
LABEL org.opencontainers.image.description="Python library for creating Google Forms from JSON"
LABEL org.opencontainers.image.source="https://github.com/andhit-r/gformlib"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="Andhitia Rama <andhitia.r@gmail.com>"

# Create a non-root user
RUN addgroup --system gformlib && adduser --system --ingroup gformlib gformlib

WORKDIR /app

# Copy the built wheel from the builder stage and install it
COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Switch to non-root user
USER gformlib

# The image exposes the library; consumers override CMD/ENTRYPOINT
CMD ["python", "-c", "import gformlib; print(f'gformlib {gformlib.__version__} ready.')"]
