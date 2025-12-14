#!/bin/bash
# NoLeet Production Deployment Script

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-noleet}"
HELM_CHART_PATH="./helm"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io/noleet}"
DOCKER_TAG="${DOCKER_TAG:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if helm is available
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed or not in PATH"
        exit 1
    fi

    # Check if docker is available
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed or not in PATH"
        exit 1
    fi

    # Check kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log_success "Pre-deployment checks passed"
}

# Build and push Docker image
build_and_push_image() {
    log_info "Building and pushing Docker image..."

    # Build the image
    docker build -t "${DOCKER_REGISTRY}/noleet:${DOCKER_TAG}" \
                 -f deployment/docker/Dockerfile .

    # Push the image
    docker push "${DOCKER_REGISTRY}/noleet:${DOCKER_TAG}"

    log_success "Docker image built and pushed: ${DOCKER_REGISTRY}/noleet:${DOCKER_TAG}"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"

    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # Label namespace
    kubectl label namespace "$NAMESPACE" name=noleet --overwrite

    log_success "Namespace created: $NAMESPACE"
}

# Create secrets
create_secrets() {
    log_info "Creating secrets..."

    # Create TLS secret (if certificates exist)
    if [ -f "deployment/ssl/tls.crt" ] && [ -f "deployment/ssl/tls.key" ]; then
        kubectl create secret tls noleet-tls \
            --cert=deployment/ssl/tls.crt \
            --key=deployment/ssl/tls.key \
            --namespace="$NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi

    # Create application secrets
    kubectl create secret generic noleet-secrets \
        --from-literal=database-url="${DATABASE_URL:-postgresql://noleet:changeme@noleet-postgresql:5432/noleet}" \
        --from-literal=redis-url="${REDIS_URL:-redis://:changeme@noleet-redis:6379/0}" \
        --from-literal=secret-key="${SECRET_KEY:-changeme-super-secret-key}" \
        --from-literal=openai-api-key="${OPENAI_API_KEY:-sk-changeme}" \
        --from-literal=anthropic-api-key="${ANTHROPIC_API_KEY:-sk-ant-changeme}" \
        --from-literal=leetcode-session-cookie="${LEETCODE_SESSION_COOKIE:-changeme}" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -

    log_success "Secrets created"
}

# Deploy with Helm
deploy_with_helm() {
    log_info "Deploying with Helm..."

    # Add required helm repositories
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo add elastic https://helm.elastic.co
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update

    # Create values file with environment-specific overrides
    cat > helm-values.yaml << EOF
global:
  imageRegistry: ${DOCKER_REGISTRY%/*}
  imagePullSecrets: []

app:
  image:
    registry: ${DOCKER_REGISTRY%/*}
    repository: noleet/noleet
    tag: ${DOCKER_TAG}

postgresql:
  auth:
    postgresPassword: "${POSTGRES_PASSWORD:-changeme}"
    password: "${POSTGRES_PASSWORD:-changeme}"

redis:
  auth:
    password: "${REDIS_PASSWORD:-changeme}"

grafana:
  adminPassword: "${GRAFANA_PASSWORD:-changeme}"

ingress:
  hosts:
    - host: ${DOMAIN:-api.noleet.ai}
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: noleet-tls
      hosts:
        - ${DOMAIN:-api.noleet.ai}
EOF

    # Deploy the chart
    helm upgrade --install noleet "$HELM_CHART_PATH" \
        --namespace "$NAMESPACE" \
        --values helm-values.yaml \
        --wait \
        --timeout 600s

    log_success "Helm deployment completed"
}

# Wait for rollout
wait_for_rollout() {
    log_info "Waiting for rollout to complete..."

    # Wait for deployments
    kubectl rollout status deployment/noleet-app \
        --namespace="$NAMESPACE" \
        --timeout=600s

    # Wait for statefulsets
    kubectl rollout status statefulset/noleet-postgresql \
        --namespace="$NAMESPACE" \
        --timeout=600s 2>/dev/null || true

    kubectl rollout status statefulset/noleet-redis \
        --namespace="$NAMESPACE" \
        --timeout=600s 2>/dev/null || true

    log_success "Rollout completed"
}

# Run post-deployment tests
run_post_deployment_tests() {
    log_info "Running post-deployment tests..."

    # Test application health
    if kubectl exec -n "$NAMESPACE" deployment/noleet-app -- curl -f http://localhost:8000/health; then
        log_success "Application health check passed"
    else
        log_error "Application health check failed"
        exit 1
    fi

    # Test database connectivity
    if kubectl exec -n "$NAMESPACE" deployment/noleet-postgresql -- pg_isready -U noleet -d noleet 2>/dev/null; then
        log_success "Database connectivity check passed"
    else
        log_warn "Database connectivity check failed (may be expected for external DB)"
    fi

    log_success "Post-deployment tests completed"
}

# Print deployment information
print_deployment_info() {
    log_info "Deployment completed successfully!"
    echo
    echo "Application URLs:"
    echo "  API: https://${DOMAIN:-api.noleet.ai}"
    echo "  Grafana: https://${DOMAIN:-monitoring.noleet.ai}/grafana"
    echo "  Prometheus: https://${DOMAIN:-monitoring.noleet.ai}/prometheus"
    echo "  Kibana: https://${DOMAIN:-monitoring.noleet.ai}/kibana"
    echo
    echo "Monitoring:"
    echo "  kubectl port-forward -n $NAMESPACE svc/noleet-grafana 3000:3000"
    echo "  kubectl port-forward -n $NAMESPACE svc/noleet-prometheus 9090:9090"
    echo
    echo "Logs:"
    echo "  kubectl logs -n $NAMESPACE deployment/noleet-app -f"
    echo "  kubectl logs -n $NAMESPACE deployment/noleet-postgresql -f"
}

# Main deployment function
main() {
    echo "🚀 NoLeet Production Deployment"
    echo "=================================="

    pre_deployment_checks
    build_and_push_image
    create_namespace
    create_secrets
    deploy_with_helm
    wait_for_rollout
    run_post_deployment_tests
    print_deployment_info

    log_success "🎉 Deployment completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    "build")
        build_and_push_image
        ;;
    "deploy")
        create_namespace
        create_secrets
        deploy_with_helm
        wait_for_rollout
        ;;
    "test")
        run_post_deployment_tests
        ;;
    *)
        main
        ;;
esac
