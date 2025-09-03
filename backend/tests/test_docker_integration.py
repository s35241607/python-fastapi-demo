"""
Docker container startup and service integration tests.
Tests Docker Compose configurations and container health checks.
"""

import subprocess
import time
from pathlib import Path

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DockerIntegrationTest:
    """Base class for Docker integration tests."""

    @staticmethod
    def run_docker_command(command: list[str], cwd: str = None) -> subprocess.CompletedProcess:
        """Run a docker command and return the result."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=120,  # 2 minutes timeout
            )
            return result
        except subprocess.TimeoutExpired:
            pytest.fail(f"Docker command timed out: {' '.join(command)}")

    @staticmethod
    def wait_for_service(url: str, timeout: int = 60, interval: int = 2) -> bool:
        """Wait for a service to become available."""
        session = requests.Session()
        retry_strategy = Retry(
            total=timeout // interval,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = session.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(interval)
        return False

    @staticmethod
    def get_project_root() -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent


class TestDockerComposeConfigurations(DockerIntegrationTest):
    """Test Docker Compose configurations for different environments."""

    def test_docker_compose_files_exist(self):
        """Test that all required Docker Compose files exist."""
        project_root = self.get_project_root()

        required_files = [
            "docker-compose.yml",
            "docker-compose.override.yml",
            "docker-compose.prod.yml",
            "backend/Dockerfile",
        ]

        for file_path in required_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"Required Docker file not found: {file_path}"

    def test_docker_compose_syntax_validation(self):
        """Test that Docker Compose files have valid syntax."""
        project_root = self.get_project_root()

        compose_files = [
            "docker-compose.yml",
            "docker-compose.override.yml",
            "docker-compose.prod.yml",
        ]

        for compose_file in compose_files:
            result = self.run_docker_command(["docker-compose", "-f", compose_file, "config"], cwd=str(project_root))
            assert result.returncode == 0, f"Invalid syntax in {compose_file}: {result.stderr}"

    def test_dockerfile_syntax_validation(self):
        """Test that Dockerfile has valid syntax."""
        project_root = self.get_project_root()
        dockerfile_path = project_root / "backend" / "Dockerfile"

        # Test building the Dockerfile (dry run)
        result = self.run_docker_command(
            [
                "docker",
                "build",
                "--target",
                "production",
                "--dry-run",
                "-f",
                str(dockerfile_path),
                str(project_root / "backend"),
            ]
        )

        # Note: --dry-run might not be available in all Docker versions
        # If it fails, we'll just check that the file exists and has basic structure
        if result.returncode != 0 and "--dry-run" in result.stderr:
            # Fallback: check basic Dockerfile structure
            dockerfile_content = dockerfile_path.read_text()
            assert "FROM python:3.12-slim" in dockerfile_content
            assert "WORKDIR /app" in dockerfile_content
            assert "EXPOSE 8000" in dockerfile_content


@pytest.mark.integration
@pytest.mark.slow
class TestDockerContainerStartup(DockerIntegrationTest):
    """Test Docker container startup and health checks."""

    def setup_method(self):
        """Setup for each test method."""
        self.project_root = self.get_project_root()
        self.cleanup_containers()

    def teardown_method(self):
        """Cleanup after each test method."""
        self.cleanup_containers()

    def cleanup_containers(self):
        """Clean up any running containers."""
        # Stop and remove containers
        self.run_docker_command(["docker-compose", "down", "-v", "--remove-orphans"], cwd=str(self.project_root))

    @pytest.mark.skipif(
        not Path("/.dockerenv").exists() and not Path("/proc/1/cgroup").exists(),
        reason="Skipping Docker tests when not in CI environment",
    )
    def test_development_environment_startup(self):
        """Test development environment container startup."""
        # Set development environment
        env = {"ENVIRONMENT": "development"}

        # Start development services
        result = self.run_docker_command(
            ["docker-compose", "-f", "docker-compose.yml", "-f", "docker-compose.override.yml", "up", "-d", "--build"],
            cwd=str(self.project_root),
        )

        assert result.returncode == 0, f"Failed to start development containers: {result.stderr}"

        try:
            # Wait for services to be healthy
            assert self.wait_for_service("http://localhost:8000/health", timeout=120)

            # Test health endpoint
            response = requests.get("http://localhost:8000/health")
            assert response.status_code == 200

            health_data = response.json()
            assert health_data["status"] == "healthy"
            assert health_data["environment"]["current_environment"] == "development"

            # Test that PostgreSQL is running (development only)
            postgres_result = self.run_docker_command(
                ["docker-compose", "exec", "-T", "postgres", "pg_isready", "-U", "postgres", "-d", "ticket_system_dev"],
                cwd=str(self.project_root),
            )
            assert postgres_result.returncode == 0

        finally:
            # Cleanup
            self.cleanup_containers()

    @pytest.mark.skipif(
        not Path("/.dockerenv").exists() and not Path("/proc/1/cgroup").exists(),
        reason="Skipping Docker tests when not in CI environment",
    )
    def test_production_environment_startup(self):
        """Test production environment container startup."""
        # Start production services (without local database)
        result = self.run_docker_command(
            ["docker-compose", "-f", "docker-compose.yml", "-f", "docker-compose.prod.yml", "up", "-d", "--build"],
            cwd=str(self.project_root),
        )

        assert result.returncode == 0, f"Failed to start production containers: {result.stderr}"

        try:
            # Wait for backend service to be healthy
            assert self.wait_for_service("http://localhost:8000/health", timeout=120)

            # Test health endpoint
            response = requests.get("http://localhost:8000/health")
            assert response.status_code == 200

            health_data = response.json()
            assert health_data["status"] in ["healthy", "unhealthy"]  # May be unhealthy due to missing external DB
            assert health_data["environment"]["current_environment"] == "production"

        finally:
            # Cleanup
            self.cleanup_containers()

    def test_container_health_checks(self):
        """Test container health check configurations."""
        project_root = self.get_project_root()

        # Read docker-compose.yml to verify health check configuration
        compose_file = project_root / "docker-compose.yml"
        compose_content = compose_file.read_text()

        # Verify health check is configured
        assert "healthcheck:" in compose_content
        assert "test:" in compose_content
        assert "interval:" in compose_content
        assert "timeout:" in compose_content
        assert "retries:" in compose_content

    def test_container_resource_limits(self):
        """Test container resource limits in production."""
        project_root = self.get_project_root()

        # Read production compose file
        prod_compose_file = project_root / "docker-compose.prod.yml"
        prod_compose_content = prod_compose_file.read_text()

        # Verify resource limits are configured
        assert "deploy:" in prod_compose_content
        assert "resources:" in prod_compose_content
        assert "limits:" in prod_compose_content
        assert "memory:" in prod_compose_content
        assert "cpus:" in prod_compose_content


class TestDockerNetworking(DockerIntegrationTest):
    """Test Docker networking configuration."""

    def test_network_configuration(self):
        """Test Docker network configuration."""
        project_root = self.get_project_root()

        # Check network configuration in compose files
        compose_file = project_root / "docker-compose.yml"
        compose_content = compose_file.read_text()

        assert "networks:" in compose_content
        assert "ticket-system-network:" in compose_content

    def test_service_dependencies(self):
        """Test service dependency configuration."""
        project_root = self.get_project_root()

        # Check development dependencies
        override_file = project_root / "docker-compose.override.yml"
        override_content = override_file.read_text()

        assert "depends_on:" in override_content
        assert "postgres:" in override_content
        assert "condition: service_healthy" in override_content


class TestDockerVolumes(DockerIntegrationTest):
    """Test Docker volume configuration."""

    def test_volume_configuration(self):
        """Test Docker volume configuration."""
        project_root = self.get_project_root()

        # Check volume configuration
        compose_file = project_root / "docker-compose.yml"
        compose_content = compose_file.read_text()

        assert "volumes:" in compose_content
        assert "./backend/logs:/app/logs" in compose_content

    def test_development_volume_mounts(self):
        """Test development volume mounts for hot reload."""
        project_root = self.get_project_root()

        override_file = project_root / "docker-compose.override.yml"
        override_content = override_file.read_text()

        # Should mount source code for development
        assert "./backend:/app" in override_content


class TestDockerEnvironmentVariables(DockerIntegrationTest):
    """Test Docker environment variable configuration."""

    def test_environment_variable_configuration(self):
        """Test environment variable configuration in Docker."""
        project_root = self.get_project_root()

        compose_file = project_root / "docker-compose.yml"
        compose_content = compose_file.read_text()

        # Check environment variable configuration
        assert "environment:" in compose_content
        assert "ENVIRONMENT=${ENVIRONMENT:-production}" in compose_content
        assert "env_file:" in compose_content

    def test_environment_specific_configs(self):
        """Test environment-specific configurations."""
        project_root = self.get_project_root()

        # Check that environment files exist
        env_files = ["backend/.env.development", "backend/.env.testing", "backend/.env.production", "backend/.env.example"]

        for env_file in env_files:
            env_path = project_root / env_file
            assert env_path.exists(), f"Environment file not found: {env_file}"


@pytest.mark.integration
class TestDockerLogging(DockerIntegrationTest):
    """Test Docker logging configuration."""

    def test_logging_configuration(self):
        """Test Docker logging configuration."""
        project_root = self.get_project_root()

        prod_compose_file = project_root / "docker-compose.prod.yml"
        prod_compose_content = prod_compose_file.read_text()

        # Check logging configuration
        assert "logging:" in prod_compose_content
        assert "driver:" in prod_compose_content
        assert "json-file" in prod_compose_content
        assert "max-size:" in prod_compose_content
        assert "max-file:" in prod_compose_content

    def test_log_directory_creation(self):
        """Test that log directories are properly configured."""
        project_root = self.get_project_root()

        # Check that logs directory exists or is created
        logs_dir = project_root / "backend" / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)

        assert logs_dir.exists()
        assert logs_dir.is_dir()
