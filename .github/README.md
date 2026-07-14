# GitHub CI/CD Pipeline

This repository includes GitHub Actions workflows for continuous integration and deployment.

## CI Pipeline (`.github/workflows/ci.yml`)

Runs on every push to `main`/`develop` branches and on pull requests:

### Jobs

1. **lint** - Runs `make lint` to check code style
2. **format-check** - Verifies backend code formatting with ruff
3. **test-backend** - Runs backend unit tests via `make test-backend`
4. **test-frontend** - Runs frontend unit tests via `make test-frontend`
5. **test-e2e** - Runs end-to-end tests via `make test-e2e`
6. **build** - Builds all Docker images (only runs if all tests pass)

All jobs use Docker Buildx and run commands from the Makefile.

## CD Pipeline (`.github/workflows/cd.yml`)

Runs on pushes to `main` branch and can be triggered manually via `workflow_dispatch`.

### Jobs

1. **build-and-push** - Builds and pushes Docker images to Docker Hub (optional)
2. **deploy** - Deploys to your server via SSH (optional)

## Setup

### Required Secrets (for CD)

To enable the CD pipeline, add these secrets to your GitHub repository:

**For Docker Hub pushes:**
- `DOCKER_HUB_USERNAME` - Your Docker Hub username
- `DOCKER_HUB_TOKEN` - Docker Hub access token (create at https://hub.docker.com/settings/security)

**For SSH deployment:**
- `SSH_HOST` - Your server hostname or IP
- `SSH_USERNAME` - SSH username on the server
- `SSH_PRIVATE_KEY` - Private SSH key for authentication

### Server Setup (for deployment)

On your deployment server:

```bash
# Clone the repository
sudo mkdir -p /opt/landmap
sudo chown $USER:$USER /opt/landmap
git clone <your-repo-url> /opt/landmap
cd /opt/landmap

# Create .env file with your production settings
cp .env.example .env
# Edit .env with your values

# Start the stack
make up
```

The deployment script assumes your code is at `/opt/landmap`. Adjust the path in `cd.yml` if needed.

## Local Testing

To test workflows locally before pushing:

```bash
# Run the full CI suite
make lint
make test
make build

# Or test individually
make test-backend
make test-frontend
make test-e2e
```

## Docker Image Tags

When pushing to Docker Hub, images are tagged with:
- `latest` - Always points to the most recent build
- `<commit-sha>` - Immutable reference to a specific commit

Example: `yourusername/landmap-backend:abc1234`