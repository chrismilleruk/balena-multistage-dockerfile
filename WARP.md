# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a demonstration repository showing how to leverage multi-stage Dockerfiles with docker-compose overrides for balena development. The architecture uses stage targeting to differentiate between production and development builds.

## Architecture

### Multi-stage Dockerfile Pattern

The `Dockerfile.template` uses a three-stage build pattern:

1. **`build` stage**: Contains compilation steps and build-time dependencies
2. **`prod` stage**: Imports artifacts from `build`, excludes scaffolding, production-ready
3. **`dev` stage**: Imports from `build` with full dev tooling, must be the last stage

**Critical constraint**: The `dev` stage MUST remain the final stage in the Dockerfile for balena's live-reload to function in local mode.

### Docker Compose Overrides

- `docker-compose.yml`: Targets `prod` stage for production deployments
- `docker-compose.dev.yml`: Overrides with `target: dev` for local development
- The dev override is automatically applied during `balena push --local` but NOT during `balena build`

### Balena Template Variables

The Dockerfile uses `%%BALENA_MACHINE_NAME%%` which is substituted by balena CLI at build time based on the target device type.

## Common Commands

### Building Specific Stages

```bash
# Build production stage
balena build --target prod -t imagename:tag .

# Build dev stage
balena build --target dev -t imagename:tag .

# Build without specifying target (builds all stages, uses last one)
balena build -t imagename:tag .
```

### Local Development

```bash
# Push to local device (automatically uses docker-compose.dev.yml)
balena push <device-ip> --local

# The dev override with live-reload only works in local mode push
```

## Development Workflow

When modifying the Dockerfile:
- Always add new stages BEFORE the `dev` stage
- If adding a `test` stage, place it between `prod` and `dev`
- Maintain the stage order: `build` → `prod` → [optional stages] → `dev`
- Remember that `docker-compose.dev.yml` merging only works during local mode push, not during build operations
