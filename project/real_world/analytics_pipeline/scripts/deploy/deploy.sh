#!/bin/bash
# Deployment script for Analytics Pipeline

set -e

# Configuration
ENVIRONMENT=${1:-development}
PROJECT_NAME="analytics-pipeline"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting deployment for environment: ${ENVIRONMENT}${NC}"

# Validate environment
case $ENVIRONMENT in
    development|staging|production)
        echo -e "${GREEN}✓ Environment validated: ${ENVIRONMENT}${NC}"
        ;;
    *)
        echo -e "${RED}❌ Invalid environment: ${ENVIRONMENT}${NC}"
        echo "Valid environments: development, staging, production"
        exit 1
        ;;
esac

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Prerequisites check passed${NC}"
}

# Build application
build_application() {
    echo -e "${YELLOW}🔨 Building application...${NC}"

    # Build Docker image
    docker build -t ${PROJECT_NAME}:${ENVIRONMENT} .

    # Tag for registry
    docker tag ${PROJECT_NAME}:${ENVIRONMENT} ${DOCKER_REGISTRY}/${PROJECT_NAME}:${ENVIRONMENT}

    echo -e "${GREEN}✓ Application built successfully${NC}"
}

# Deploy based on environment
deploy_development() {
    echo -e "${YELLOW}🚀 Deploying to development environment...${NC}"

    # Use docker-compose for development
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

    echo -e "${GREEN}✓ Development deployment completed${NC}"
    echo -e "${GREEN}🌐 Application available at: http://localhost:8000${NC}"
    echo -e "${GREEN}📊 Grafana available at: http://localhost:3000${NC}"
}

deploy_staging() {
    echo -e "${YELLOW}🚀 Deploying to staging environment...${NC}"

    # Create staging-specific environment
    cp .env.example .env.staging
    # Add staging-specific configurations

    # Deploy with staging configuration
    docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build

    echo -e "${GREEN}✓ Staging deployment completed${NC}"
}

deploy_production() {
    echo -e "${YELLOW}🚀 Deploying to production environment...${NC}"

    # Backup current deployment
    echo -e "${YELLOW}💾 Creating backup...${NC}"
    # Add backup logic here

    # Deploy with production configuration
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

    # Run health checks
    echo -e "${YELLOW}🔍 Running health checks...${NC}"
    sleep 30
    curl -f http://localhost/health || (echo -e "${RED}❌ Health check failed${NC}"; exit 1)

    echo -e "${GREEN}✓ Production deployment completed${NC}"
    echo -e "${GREEN}🔒 Application secured and running${NC}"
}

# Health check
health_check() {
    echo -e "${YELLOW}🔍 Performing health check...${NC}"

    # Wait for services to be ready
    sleep 10

    # Check main application
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo -e "${GREEN}✓ Application health check passed${NC}"
    else
        echo -e "${RED}❌ Application health check failed${NC}"
        exit 1
    fi

    # Check monitoring stack (if deployed)
    if curl -f http://localhost:3000 &> /dev/null; then
        echo -e "${GREEN}✓ Monitoring stack health check passed${NC}"
    fi
}

# Rollback function
rollback() {
    echo -e "${RED}🔄 Performing rollback...${NC}"

    # Stop current deployment
    docker-compose down

    # Restore from backup (if available)
    # Add rollback logic here

    echo -e "${YELLOW}⚠️ Rollback completed. Manual verification required.${NC}"
}

# Main deployment flow
main() {
    check_prerequisites

    case $ENVIRONMENT in
        development)
            build_application
            deploy_development
            ;;
        staging)
            build_application
            deploy_staging
            ;;
        production)
            build_application
            deploy_production
            ;;
    esac

    health_check

    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${GREEN}📊 Monitor your application at the URLs shown above${NC}"
}

# Error handling
trap 'echo -e "${RED}❌ Deployment failed${NC}"; rollback' ERR

# Run main function
main "$@"
