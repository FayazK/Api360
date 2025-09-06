#!/bin/bash

# Activate the virtual environment
source fastenv/bin/activate

# Run the application in development mode
uvicorn app.main:app --reload
