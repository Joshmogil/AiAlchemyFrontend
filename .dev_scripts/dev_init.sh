#!/bin/bash

# This script is used to initialize the development environment.
source .dev_scripts/envs

$PYTHON -m venv .venv
echo "run 'source .venv/bin/activate' to activate the virtual environment"
