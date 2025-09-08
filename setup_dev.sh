#!/bin/bash

cp .env.example .env

# Create a virtual environment
python3 -m venv fastenv

# Activate the virtual environment
source fastenv/bin/activate

# Install dependencies
pip install -r requirements.txt
