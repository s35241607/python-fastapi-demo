# Docker development helper script for Windows PowerShell

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("setup", "start", "stop", "restart", "logs", "test", "clean", "status")]
    [string]$Command,
    
    [Parameter(Mandatory=$false)]
    [string]$Service
)

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if Docker is running
function Test-Docker {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        Write-Error "Docker is not running. Please start Docker and try again."
        exit 1
    }
}

# Function to setup development environment
function Start-DevEnvironment {
    Write-Status "Setting up development environment..."
    
    # Create .env file if it doesn't exist
    if (-not (Test-Path ".env")) {
        Write-Status "Creating .env file from template..."
        Copy-Item ".env.example" ".env"
        Write-Warning "Please review and update the .env file with your settings."
    }
    
    # Create logs directory
    if (-not (Test-Path "backend/logs")) {
        New-Item -ItemType Directory -Path "backend/logs" -Force | Out-Null
    }
    
    # Build and start services
    Write-Status "Building and starting development services..."
    docker-compose up --build -d
    
    Write-Status "Development environment is ready!"
    Write-Status "Backend API: http://localhost:8000"
    Write-Status "API Documentation: http://localhost:8000/docs"
    Write-Status "pgAdmin: http://localhost:5050 (admin@example.com / admin)"
}

# Function to stop services
function Stop-Services {
    Write-Status "Stopping all services..."
    docker-compose down
}

# Function to clean up
function Remove-DockerResources {
    Write-Status "Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker system prune -f
}

# Function to show logs
function Show-Logs {
    param([string]$ServiceName)
    
    if ([string]::IsNullOrEmpty($ServiceName)) {
        docker-compose logs -f
    } else {
        docker-compose logs -f $ServiceName
    }
}

# Function to run tests
function Invoke-Tests {
    Write-Status "Running tests in Docker container..."
    docker-compose exec backend pytest
}

# Main script logic
switch ($Command) {
    { $_ -in @("setup", "start") } {
        Test-Docker
        Start-DevEnvironment
    }
    "stop" {
        Stop-Services
    }
    "restart" {
        Test-Docker
        Stop-Services
        Start-DevEnvironment
    }
    "logs" {
        Show-Logs -ServiceName $Service
    }
    "test" {
        Invoke-Tests
    }
    "clean" {
        Remove-DockerResources
    }
    "status" {
        docker-compose ps
    }
}

Write-Host "Script completed successfully!" -ForegroundColor Green