#!/bin/bash

function help() {
    echo "Usage: ./tf.sh [command]"
    echo
    echo "Commands:"
    echo "  init      - Initialize Terraform"
    echo "  up        - Create or update infrastructure"
    echo "  down      - Destroy infrastructure"
    echo "  stop      - Stop the kind cluster (can be restarted later)"
    echo "  start     - Start a previously stopped kind cluster"
    echo "  clean     - Clean up all local state"
    echo "  logs      - View logs (backend or postgres)"
    echo "  reload    - Restart the backend pod to pick up changes"
    echo "  docker    - View Docker build logs manually"
    echo "  help      - Show this help message"
}

function init() {
    terraform init
}

function up() {
    export TF_LOG=WARN
    terraform apply -auto-approve
}

function down() {
    terraform destroy -auto-approve
}

function stop() {
    echo "Stopping kind cluster container..."
    if docker ps -q --filter "name=amoneyplan-control-plane" | grep -q .; then
        docker stop amoneyplan-control-plane
        echo "Kind cluster stopped. Use './tf.sh start' to restart it."
    else
        echo "Kind cluster container not found or already stopped."
    fi
}

function start() {
    echo "Starting kind cluster container..."
    if docker ps -a -q --filter "name=amoneyplan-control-plane" | grep -q .; then
        docker start amoneyplan-control-plane
        echo "Waiting for cluster to be ready..."
        sleep 5
        kubectl wait --for=condition=ready nodes --all --timeout=60s
        echo "Kind cluster started."
    else
        echo "Kind cluster container not found. Use 'up' command to create a new cluster."
    fi
}

function clean() {
    rm -rf .terraform .terraform.lock.hcl terraform.tfstate terraform.tfstate.backup
}

function logs() {
    if [ -z "$2" ]; then
        echo "Please specify a component (backend or postgres)"
        exit 1
    fi

    case "$2" in
        backend)
            kubectl -n amoneyplan logs -f deployment/backend
            ;;
        postgres)
            kubectl -n amoneyplan logs -f deployment/postgres
            ;;
        *)
            echo "Invalid component. Use 'backend' or 'postgres'"
            exit 1
            ;;
    esac
}

function reload() {
    echo "Restarting backend pod..."
    kubectl -n amoneyplan rollout restart deployment backend
    kubectl -n amoneyplan rollout status deployment backend
}

function docker_logs() {
    echo "Building Docker image manually to see logs..."
    cd ../../backend
    docker build -t amoneyplan-backend:latest .
}

case "$1" in
    init)
        init
        ;;
    up)
        up
        ;;
    down)
        down
        ;;
    stop)
        stop
        ;;
    start)
        start
        ;;
    clean)
        clean
        ;;
    logs)
        logs "$@"
        ;;
    reload)
        reload
        ;;
    docker)
        docker_logs
        ;;
    *)
        help
        ;;
esac
