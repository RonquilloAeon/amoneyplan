#!/bin/bash

function help() {
    echo "Usage: ./tf.sh [command]"
    echo
    echo "Commands:"
    echo "  init      - Initialize Terraform"
    echo "  up        - Create or update infrastructure"
    echo "  down      - Destroy infrastructure"
    echo "  clean     - Clean up all local state"
    echo "  logs      - View logs (backend or postgres)"
    echo "  reload    - Restart the backend pod to pick up changes"
    echo "  help      - Show this help message"
}

function init() {
    terraform init
}

function up() {
    terraform apply -auto-approve
}

function down() {
    terraform destroy -auto-approve
}

function clean() {
    rm -rf .terraform .terraform.lock.hcl terraform.tfstate terraform.tfstate.backup
}

function reload() {
    echo "Restarting backend pod..."
    kubectl -n amoneyplan rollout restart deployment backend
    kubectl -n amoneyplan rollout status deployment backend
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
    clean)
        clean
        ;;
    reload)
        reload
        ;;
    logs)
        logs "$@"
        ;;
    *)
        help
        ;;
esac