# FastAPI Microservice Template

This repository provides a modular FastAPI microservice targeting Python 3.12+ (Python 3.14 recommended) with production-ready building blocks:

- Correlation IDs on every request/response
- Structured logging with PII scrubbing
- Rate limiting backed by Redis
- JWT authentication middleware
- Centralised exception handling with correlation IDs
- Environment management via `.env` and AWS Secrets Manager
- MySQL (SQLAlchemy) CRUD example
- OpenSearch integrations
- Redis-backed caching helpers
- RabbitMQ producer/consumer modules

## Project Layout

```
app/
  core/              # configuration, logging, exceptions, correlation ids
  middlewares/       # correlation id, logging, JWT auth
  dependencies/      # shared FastAPI dependencies (rate limiting)
  models/            # SQLAlchemy models
  schemas/           # Pydantic schemas
  routers/           # API routers (users, search, cache, messages, health)
  services/          # Integrations (database, cache, search, messaging, secrets)
  utils/             # PII scrubbing helpers
  main.py            # FastAPI application factory & lifespan hooks
```

## Getting Started

1. **Install Python** (macOS)
   - Use Python 3.12 or newer (Python 3.14 is the latest stable version).
   
   **Option 1: Using Homebrew (Recommended)**
   ```bash
   # Install Homebrew if you don't have it
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install the latest Python (currently 3.14)
   brew install python@3.14
   
   # Or install a specific version (e.g., 3.12, 3.13, 3.14)
   # brew install python@3.12
   
   # Verify installation
   python3.14 --version
   ```
   
   **Important: PATH Configuration**
   
   After installing Python via Homebrew, you may notice that `python3 --version` still shows an older version (e.g., 3.9.6). This happens because:
   - macOS includes a system Python at `/usr/bin/python3`
   - Homebrew installs Python at `/opt/homebrew/bin/python3.14` (Apple Silicon) or `/usr/local/bin/python3.14` (Intel)
   - The system Python takes precedence if Homebrew's bin directory isn't first in your PATH
   
   **Solution 1: Use the version-specific command** (Recommended for this project)
   ```bash
   # Always use the version-specific command
   python3.14 --version  # Should show Python 3.14.x
   python3.14 -m venv .venv  # Create venv with Python 3.14
   ```
   
   **Solution 2: Update your PATH** (To make `python3` point to Homebrew's Python)
   ```bash
   # For Apple Silicon Macs (M1/M2/M3)
   echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
   
   # For Intel Macs
   # echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
   
   # Reload your shell configuration
   source ~/.zshrc
   
   # Verify
   which python3  # Should show /opt/homebrew/bin/python3 (or /usr/local/bin/python3)
   python3 --version  # Should now show Python 3.14.x
   ```
   
   **Note**: For this project, using `python3.14` explicitly is recommended to avoid version conflicts.
   
   **Option 2: Using pyenv (For managing multiple Python versions)**
   ```bash
   # Install pyenv via Homebrew
   brew install pyenv
   
   # Add to your shell profile (~/.zshrc or ~/.bash_profile)
   echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
   echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
   echo 'eval "$(pyenv init -)"' >> ~/.zshrc
   source ~/.zshrc
   
   # Install the latest Python (currently 3.14)
   pyenv install 3.14
   pyenv global 3.14
   
   # Verify installation
   python --version
   ```
   
   **Option 3: Official Python Installer**
   - Download Python 3.14 (or 3.12+) from [python.org](https://www.python.org/downloads/)
   - Run the installer and follow the installation wizard
   - Verify installation: `python3 --version`

2. **Create a virtual environment**
   ```bash
   # Use the version-specific Python command to ensure correct version
   python3.14 -m venv .venv
   source .venv/bin/activate
   
   # Verify the Python version in the virtual environment
   python --version  # Should show Python 3.14.x
   ```
   
   **Note**: If you see a version mismatch, make sure you're using `python3.14` (or `python3.12`, `python3.13`) instead of just `python3` to explicitly use the Homebrew-installed version.

3. **Install dependencies**
   ```bash
   pip install -U pip
   pip install -e .
   ```
   
   **Command Explanations:**
   
   - **`pip install -U pip`**: 
     - Upgrades pip (Python package installer) to the latest version
     - The `-U` flag stands for `--upgrade`
     - Ensures you have the latest pip features, bug fixes, and security patches
     - Recommended before installing project dependencies to avoid compatibility issues
   
   - **`pip install -e .`**:
     - Installs the current project in **editable mode** (also called "development mode")
     - The `-e` flag stands for `--editable`
     - The `.` refers to the current directory (where `pyproject.toml` is located)
     - **Editable mode** means:
       - The package is linked to your source code directory
       - Changes to your code are immediately reflected without reinstalling
       - Perfect for development - you can edit code and see changes instantly
       - Installs all dependencies listed in `pyproject.toml`
       - Creates a link in your Python environment pointing to your project directory
   
   **What gets installed:**
   - All dependencies listed in `pyproject.toml` (fastapi, uvicorn, pydantic, etc.)
   - The project itself as a package (so you can import from `app` module)
   - All packages are installed in your virtual environment's `site-packages` directory
   
   **Note**: Uvicorn (the ASGI server) is already included in the project dependencies and will be installed automatically. No separate installation is required. You can verify the installation by running:
   ```bash
   uvicorn --version
   ```
   
   If for some reason you need to install uvicorn separately (not recommended), you can run:
   ```bash
   pip install "uvicorn[standard]>=0.38.0"
   ```

4. **Environment variables**
   - Copy `.env.example` to `.env` and adjust values.
   - `AUTH_EXEMPT_PATHS` contains endpoints that bypass JWT checks (comma-separated).
   - Provide connection strings for MySQL, Redis, OpenSearch, and RabbitMQ.
   
   **AWS Secrets Manager Configuration:**
   - `AWS_REGION`: AWS region where the secret is stored (e.g., `us-east-1`)
   - `AWS_SECRETS_MANAGER_SECRET_NAME`: Name or ARN of the secret in AWS Secrets Manager
   
   **AWS Authentication (choose one method):**
   
   **Option 1: Environment Variables** (for local development)
   ```bash
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_SESSION_TOKEN=your_session_token  # Optional, only for temporary credentials
   ```
   
   **Option 2: AWS Credentials File** (recommended for local development)
   ```bash
   # Create ~/.aws/credentials file
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
   ```
   
   **Option 3: IAM Roles** (for EC2/ECS/Lambda - no credentials needed)
   - Attach an IAM role with `secretsmanager:GetSecretValue` permission
   - Boto3 automatically uses the instance/container role
   
   **Note**: The application uses boto3's default credential chain, which automatically discovers credentials in the order listed above. See the [AWS Secrets Manager section](#aws-secrets-manager-authentication) for more details.

5. **Install Docker** (macOS)
   
   Docker is required to run the infrastructure services (MySQL, Redis, OpenSearch, RabbitMQ) locally. Choose one of the following installation methods:
   
   **Option 1: Docker Desktop (Recommended)**
   
   Docker Desktop is the easiest way to run Docker on macOS. It includes Docker Engine, Docker CLI, and a graphical user interface.
   
   ```bash
   # Install via Homebrew (easiest method)
   brew install --cask docker
   
   # Or download directly from Docker's website
   # Visit: https://www.docker.com/products/docker-desktop/
   # Download Docker Desktop for Mac (Apple Silicon or Intel)
   ```
   
   **After Installation:**
   
   1. **Launch Docker Desktop**: Open Docker Desktop from Applications or Spotlight
   2. **Complete Setup**: Follow the setup wizard (accept terms, configure settings)
   3. **Verify Installation**: Open a terminal and run:
      ```bash
      docker --version
      docker-compose --version
      ```
      You should see version numbers for both commands.
   
   4. **Test Docker**: Run a test container to ensure Docker is working:
      ```bash
      docker run hello-world
      ```
      You should see a "Hello from Docker!" message.
   
   **Docker Desktop Features:**
   - Graphical interface for managing containers and images
   - Automatic updates
   - Resource management (CPU, memory limits)
   - Built-in Kubernetes support (optional)
   - Easy volume and network management
   
   **Option 2: Colima (Lightweight Alternative)**
   
   Colima is a lightweight alternative to Docker Desktop that runs Docker containers using Lima (Linux virtual machines).
   
   ```bash
   # Install via Homebrew
   brew install colima docker docker-compose
   
   # Start Colima
   colima start
   
   # Verify installation
   docker --version
   docker run hello-world
   ```
   
   **Colima Benefits:**
   - Lower resource usage than Docker Desktop
   - No GUI (command-line only)
   - Free and open-source
   - Good for development environments
   
   **System Requirements:**
   - macOS 10.15 (Catalina) or later
   - At least 4GB RAM (8GB+ recommended)
   - VirtualBox or HyperKit (for older Macs) / Apple Virtualization Framework (for Apple Silicon)
   
   **Troubleshooting:**
   
   - **Docker daemon not running**: Make sure Docker Desktop is running (check the menu bar icon)
   - **Permission denied**: You may need to add your user to the docker group or restart Docker Desktop
   - **Port already in use**: If you see port conflicts, stop existing containers:
     ```bash
     docker ps -a  # List all containers
     docker stop <container_name>  # Stop a specific container
     docker rm <container_name>  # Remove a container
     ```
   
   **Note**: For this project, Docker Desktop is recommended as it provides the easiest setup and management experience.

6. **Run infrastructure services** (using Docker):
   
   Once Docker is installed and running, you can start the required infrastructure services with the following commands:
   
   ```bash
   # MySQL database
   docker run --name mysql -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=sampledb -p 3306:3306 -d mysql:8
   
   # Redis cache and rate limiting backend
   docker run --name redis -p 6379:6379 -d redis:7
   
   # OpenSearch for search functionality
   docker run --name opensearch -p 9200:9200 -e "discovery.type=single-node" opensearchproject/opensearch:2
   docker run --name opensearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=itsfuntodevelopaisoftware@123D" \
  opensearchproject/opensearch:2
   
   # RabbitMQ for messaging
   docker run --name rabbitmq -p 5672:5672 -p 15672:15672 -d rabbitmq:3-management
   ```
   
   **What these commands do:**
   - `--name <name>`: Assigns a friendly name to the container
   - `-e <key>=<value>`: Sets environment variables inside the container
   - `-p <host_port>:<container_port>`: Maps ports from host to container
   - `-d`: Runs the container in detached mode (background)
   - `<image>:<tag>`: Specifies the Docker image and version to use
   
   **Verify containers are running:**
   ```bash
   docker ps
   ```
   You should see all four containers (mysql, redis, opensearch, rabbitmq) in the list.
   
   **Access service UIs:**
   - **RabbitMQ Management**: http://localhost:15672 (default: guest/guest)
   - **OpenSearch**: http://localhost:9200
   
   **Stop containers** (when done):
   ```bash
   docker stop mysql redis opensearch rabbitmq
   ```
   
   **Start containers again** (if they were stopped but not removed):
   ```bash
   docker start mysql redis opensearch rabbitmq
   ```
   
   **Remove containers** (to start fresh):
   ```bash
   docker rm -f mysql redis opensearch rabbitmq
   ```

7. **Generate a JWT token for testing**
   
   Protected endpoints require a Bearer token that matches the application’s JWT settings. The service does **not** issue tokens, so generate one manually (or use your IdP).
   
   1. Check your JWT settings (defaults or `.env`):
      - `JWT_SECRET` (default: `changeme`)
      - `JWT_ALGORITHM` (default: `HS256`)
      - Optional: `JWT_AUDIENCE`, `JWT_ISSUER`
   
   2. Generate a token with `python-jose`:
      ```bash
      python - <<'PY'
      from datetime import datetime, timedelta, timezone
      from jose import jwt

      secret = "changeme"          # match JWT_SECRET
      algorithm = "HS256"          # match JWT_ALGORITHM
      claims = {
          "sub": "user@example.com",
          "role": "admin",
          "exp": datetime.now(timezone.utc) + timedelta(hours=1),
          # Uncomment if your config requires them:
          # "aud": "fastapi-clients",
          # "iss": "fastapi-service",
      }

      token = jwt.encode(claims, secret, algorithm=algorithm)
      print(token)
      PY
      ```
   
   3. Prefer a reusable script? Use the helper under `scripts/`:
      ```bash
      pip install "python-jose[cryptography]"  # once per environment
      python scripts/generate_jwt.py --sub user@example.com --role admin --hours 2
      ```
      - The script automatically loads `.env` from the project root and falls back to environment variables/defaults, so generated tokens always match your configuration.
      - Override any parameter via flags (e.g., `--secret mysecret`, `--aud api-clients`).
   
   4. Call protected endpoints with:
      ```
      Authorization: Bearer <token>
      ```
   5. If you change `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_AUDIENCE`, or `JWT_ISSUER`, regenerate the token with matching values (either via the snippet or the script).
   6. **Use JWT inside Swagger UI**:
      - Open http://localhost:8000/docs and click the green “Authorize” button.
      - Paste the token (just the JWT string, no `Bearer ` prefix) into the dialog and click *Authorize*.
      - All protected endpoints invoked via Swagger will now include the `Authorization: Bearer` header until you click *Logout*.
   
8. **Launch the API**
   ```bash
   uvicorn app.main:app --reload
   ```

The interactive docs are available at `http://localhost:8000/docs`.

### Understanding `pyproject.toml`

This project follows the modern PEP-517/518 packaging conventions. Two key sections to be aware of:

#### `[build-system]`
```toml
[build-system]
requires = ["setuptools>=80.9.0", "wheel"]
build-backend = "setuptools.build_meta"
```
- `requires`: bootstrap dependencies installed in an isolated environment before your package is built. Here we need `setuptools` ≥ 80.9.0 and `wheel`.
- `build-backend`: the module that implements the PEP 517 hooks. `setuptools.build_meta` is setuptools’ backend; tools like `pip` import it and call the standard build hooks. This replaces the old `setup.py install` flow and guarantees reproducible builds.

#### `[project]`
Farther down in `pyproject.toml` you’ll see:
```toml
[project]
name = "fast-api-service"
version = "0.1.0"
description = "Modular FastAPI microservice..."
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.121.3",
  "uvicorn[standard]>=0.38.0",
  # ...
]
```
- Defines metadata (name, version, authors, description).
- Declares Python compatibility (`requires-python`).
- Lists runtime dependencies that are installed when you run `pip install -e .`.

Other tool-specific configs live under `[tool.*]` sections. Together, this single `pyproject.toml` replaces `setup.py`, `setup.cfg`, and `requirements.txt` by providing both build instructions and metadata in a declarative, standardized format; any packaging tool can read it and build/install the project correctly.

## Using Redis, OpenSearch, and RabbitMQ APIs

Once `docker compose up --build` is running (or you started the individual containers), you can interact with each service directly:

### Redis (Cache / Rate Limiter)
```bash
redis-cli -h localhost -p 6379
# Example commands
SET greeting "hello world"
GET greeting
KEYS *
```

### OpenSearch (Search Engine)
```bash
# Check cluster health (auth disabled in docker compose; add -u admin:password if enabled)
curl http://localhost:9200/_cluster/health | jq

# Index a document
curl -XPUT http://localhost:9200/sample-index/_doc/1 \
     -H "Content-Type: application/json" \
     -d '{"title":"Test doc","description":"Created from curl"}'

# Search
curl http://localhost:9200/sample-index/_search?q=title:Test | jq
```

If security is enabled, supply `-u admin:<your password>` and use `https://localhost:9200`.

### RabbitMQ (Messaging)
```bash
# Publish a message using rabbitmqadmin (already available in the management UI)
docker exec rabbitmq rabbitmqadmin publish \
    exchange=amq.default routing_key=test.payload payload='{"hello":"world"}'

# Consume a single message
docker exec rabbitmq rabbitmqadmin get queue=test.payload count=1
```

You can also use the management interface at http://localhost:15672 (default user/pass: guest/guest) to create queues, publish messages, or monitor consumers.

## Run the Entire Stack with Docker Compose

You can run the FastAPI application **and** all dependent services (MySQL, Redis, OpenSearch, RabbitMQ) with a single command using the provided `docker-compose.yml`.

1. **Ensure Docker is running**
   - Start Docker Desktop (or Colima) before running any commands.
   - Optional: create/update your `.env` file for secrets such as `JWT_SECRET`, `AWS_REGION`, etc. (`docker-compose` automatically loads `.env` if present).

2. **Build and start all services**
   ```bash
   docker compose up --build
   ```
   - `--build` ensures the Dockerfile is rebuilt whenever dependencies change.
   - This command will start the FastAPI app plus MySQL, Redis, OpenSearch, and RabbitMQ.
   - Logs from every service will stream to your terminal.

3. **Run in the background (optional)**
   ```bash
   docker compose up --build -d
   ```
   - Use `-d` (detached mode) if you prefer the services to run in the background.
   - View logs later with `docker compose logs -f app`.

4. **Access the application**
   - FastAPI UI: http://localhost:8000/docs
   - RabbitMQ management UI: http://localhost:15672 (default user/pass: guest/guest)
   - OpenSearch cluster info: http://localhost:9200

5. **Stop the stack**
   ```bash
   docker compose down
   ```
   - This stops all containers but preserves volumes (your MySQL/OpenSearch data).
   - Remove volumes as well with `docker compose down -v` if you want a fresh start.

6. **Customize environment variables**
   - Update `.env` (or change the `environment` section inside `docker-compose.yml`) to tweak DSNs, credentials, or application settings.
   - Example `.env` entries:
     ```bash
     JWT_SECRET=changeme
     AWS_REGION=us-east-1
     AWS_SECRETS_MANAGER_SECRET_NAME=local-dev-secret
     ```

**Notes:**
- Hot reload is enabled because the project root is mounted into the `app` container (`.:/app`). Modify files locally and the container restarts automatically.
- Opensearch requires at least 4GB RAM. If the container fails to start, adjust Docker Desktop resource limits.
- The compose file sets sane defaults (admin/admin for OpenSearch, guest/guest for RabbitMQ). Update them for production usage.

## How the Application Works

### Application Architecture

This FastAPI application follows an **ASGI (Asynchronous Server Gateway Interface)** architecture, which enables high-performance async operations and concurrent request handling.

#### Request Flow

1. **Client Request** → HTTP request arrives at the server
2. **ASGI Server (Uvicorn)** → Receives and parses the HTTP request
3. **FastAPI Application** → Processes the request through middleware stack:
   - Correlation ID middleware (generates/tracks request IDs)
   - Request logging middleware (structured logging)
   - JWT authentication middleware (validates tokens)
   - CORS middleware (handles cross-origin requests)
4. **Router** → Routes request to appropriate endpoint handler
5. **Dependencies** → Injects shared dependencies (e.g., rate limiting, database sessions)
6. **Endpoint Handler** → Executes business logic (async operations)
7. **Response** → Returns JSON response through middleware stack
8. **ASGI Server** → Sends HTTP response back to client

#### Application Lifecycle

The application uses a **lifespan context manager** that handles startup and shutdown:

- **Startup**: Initializes connections to MySQL, Redis, OpenSearch, RabbitMQ, and loads AWS secrets
- **Runtime**: Handles incoming requests asynchronously
- **Shutdown**: Gracefully closes all connections and cleans up resources

### Why We Need an ASGI Server

#### What is ASGI?

**ASGI (Asynchronous Server Gateway Interface)** is a standard interface between async-capable web servers and Python web applications. It's the async successor to WSGI (Web Server Gateway Interface).

#### Key Differences: ASGI vs WSGI

| Feature | WSGI (Traditional) | ASGI (Modern) |
|---------|-------------------|---------------|
| **Concurrency Model** | Synchronous, one request per thread/process | Asynchronous, handles multiple requests concurrently |
| **I/O Operations** | Blocks during database/network calls | Non-blocking, can handle other requests while waiting |
| **WebSocket Support** | Not supported | Native support |
| **HTTP/2 & HTTP/3** | Limited support | Full support |
| **Performance** | Lower throughput under load | Higher throughput, better resource utilization |

#### Why Uvicorn?

**Uvicorn** is a lightning-fast ASGI server implementation that:

> **Note**: Uvicorn is already included in the project dependencies (`uvicorn[standard]>=0.38.0` in `pyproject.toml`). When you run `pip install -e .`, it will be installed automatically along with all other dependencies. No separate installation is required.

1. **Handles Async Operations**: Enables FastAPI to process multiple requests concurrently without blocking
2. **High Performance**: Built on `uvloop` (a fast event loop) for optimal async performance
3. **Production Ready**: Supports multiple workers, SSL/TLS, and production deployment patterns
4. **Hot Reload**: Development mode with automatic code reloading (`--reload` flag)
5. **Standards Compliant**: Implements the ASGI specification correctly

#### How Async Operations Work

When you run `uvicorn app.main:app --reload`:

```python
# Example: Multiple requests can be handled concurrently
async def get_user(user_id: int):
    # While waiting for database query, other requests can be processed
    user = await db.query("SELECT * FROM users WHERE id = ?", user_id)
    return user
```

**Without ASGI (WSGI)**: If 100 requests arrive simultaneously, you'd need 100 threads/processes (resource-intensive)

**With ASGI**: A single process can handle all 100 requests concurrently by switching between them while waiting for I/O operations (database, Redis, etc.)

#### Application Components

- **FastAPI**: The web framework that defines routes, validates requests/responses, and generates OpenAPI docs
- **Uvicorn**: The ASGI server that runs the FastAPI application and handles HTTP protocol
- **Middleware Stack**: Processes requests/responses (logging, auth, CORS, correlation IDs)
- **Routers**: Organize endpoints by domain (users, search, cache, messages, health)
- **Services**: Abstract external integrations (database, cache, search, messaging)
- **Models & Schemas**: Define data structures (SQLAlchemy models, Pydantic schemas)

#### Running in Production

For production deployments, run multiple Uvicorn workers behind a reverse proxy:

```bash
# Multiple worker processes for better performance
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# Or use Gunicorn with Uvicorn workers (recommended for production)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

This setup allows the application to:
- Handle thousands of concurrent requests
- Scale horizontally by adding more workers
- Maintain low latency even under heavy load
- Efficiently utilize server resources

## Key Features

- **Correlation IDs**: Generated or propagated via `X-Correlation-ID` header. Included in logs, exception responses, and returned headers.
- **Logging & PII scrubbing**: Structured JSON logs with configurable redaction fields (`PII_FIELDS`).
- **Rate limiting**: Uses `fastapi-limiter` backed by Redis. Default limits configured by `RATE_LIMIT_PER_MINUTE`.
- **JWT middleware**: Validates Bearer tokens, injects decoded claims into `request.state.user`. Exempt paths configurable.
- **Exception handling**: Consistent JSON error payloads with correlation IDs; validation and unhandled exceptions are captured.
- **AWS Secrets Manager**: Secrets are fetched on startup and merged into `os.environ`, enabling secure credential loading.
- **MySQL CRUD**: `users` endpoints demonstrate async SQLAlchemy operations.
- **OpenSearch integration**: Sample router to index and fetch documents asynchronously.
- **Redis caching**: Simple POST/GET endpoints to cache arbitrary payloads.
- **RabbitMQ messaging**: Producer endpoint publishes JSON messages; consumer utilities support background processing and single fetch.

## Debugging & Observability

- **Enable verbose logging**: Set `LOG_LEVEL=DEBUG` in `.env`.
- **Trace specific requests**: Use the `X-Correlation-ID` header to follow logs across services.
- **Inspect rate limiting**: Redis keys prefixed by `fastapi-limiter` track request counts.
- **Check JWT claims**: Log outputs include `request.state.user` for authenticated calls.
- **AWS secrets failures**: Startup logs warn if secrets cannot be loaded (service continues with existing env vars).

## Running Tests

Install development dependencies and run pytest:

```bash
pip install -e .[dev]
pytest
```

## AWS Secrets Manager Authentication

### How Secrets Are Fetched

The application fetches secrets from AWS Secrets Manager during startup using the `load_secrets_into_env()` function in `app/services/secrets/aws_secrets.py`. Here's how it works:

1. **Session Creation**: Creates a boto3 session with the specified AWS region
2. **Client Initialization**: Creates a Secrets Manager client
3. **Secret Retrieval**: Calls `get_secret_value()` with the secret name/ARN
4. **Environment Merge**: Parses the JSON secret and merges key-value pairs into `os.environ`
5. **Settings Reload**: If secrets are loaded, the settings are reloaded to pick up new values

### Authentication Methods

Boto3 uses a **default credential chain** to authenticate with AWS. Credentials are discovered in this order (first available is used):

1. **Environment Variables** (highest priority for explicit control)
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_SESSION_TOKEN=your_session_token  # Optional, for temporary credentials
   ```

2. **AWS Credentials File** (`~/.aws/credentials`)
   ```ini
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
   ```

3. **AWS Config File** (`~/.aws/config`)
   ```ini
   [default]
   region = us-east-1
   ```

4. **IAM Roles** (for EC2/ECS/Lambda instances)
   - Attach an IAM role to your instance/container
   - Grant `secretsmanager:GetSecretValue` permission
   - Boto3 automatically uses the instance role (no credentials needed)

5. **IAM Instance Profile** (alternative to IAM roles)

### Required Environment Variables

The following environment variables are **required** for the application to know which secret to fetch:

- `AWS_REGION`: AWS region where the secret is stored (e.g., `us-east-1`, `ap-southeast-1`)
- `AWS_SECRETS_MANAGER_SECRET_NAME`: Name or ARN of the secret in AWS Secrets Manager

### Optional Authentication Environment Variables

These are **only needed if you're not using IAM roles** (e.g., local development):

- `AWS_ACCESS_KEY_ID`: AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key  
- `AWS_SESSION_TOKEN`: AWS session token (required for temporary credentials from STS)

### Secret Format

The secret in AWS Secrets Manager should be stored as a JSON string. For example:

```json
{
  "DATABASE_PASSWORD": "my_secure_password",
  "API_KEY": "my_api_key",
  "REDIS_PASSWORD": "redis_password"
}
```

These key-value pairs will be merged into the application's environment variables, allowing them to be accessed via the `Settings` class.

### Error Handling

- If AWS authentication fails, the application logs a warning and continues with existing environment variables
- If the secret cannot be retrieved, the application logs a warning and continues startup
- This ensures the application can still run even if AWS Secrets Manager is unavailable (useful for local development)

### Best Practices

- **Local Development**: Use AWS credentials file (`~/.aws/credentials`) or environment variables
- **Production**: Use IAM roles attached to EC2 instances, ECS tasks, or Lambda functions
- **Security**: Never commit AWS credentials to version control
- **Permissions**: Follow the principle of least privilege - only grant `secretsmanager:GetSecretValue` for the specific secret
- **Rotation**: Enable automatic secret rotation in AWS Secrets Manager for sensitive credentials

## Deployment Notes

- Use a process manager (e.g., `uvicorn --workers 4`) behind a production ASGI server like `gunicorn`.
- Configure TLS for OpenSearch and secure connections for MySQL/RabbitMQ in production.
- Ensure AWS credentials are available to the runtime (via IAM role, env vars, or instance profile).


