#!/bin/bash

# Check if an argument was provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backend|frontend> [additional test arguments...]"
    exit 1
fi

# Get the target (backend/frontend)
target=$1
shift  # Remove first argument, leaving remaining args for the test command

clear

case $target in
    "backend")
        cd backend || exit 1
        nox -s test "$@"
        ;;
    "frontend")
        echo "Frontend testing not implemented yet"
        exit 1
        ;;
    *)
        echo "Error: Invalid target. Use 'backend' or 'frontend'"
        exit 1
        ;;
esac
