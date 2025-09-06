#!/bin/bash

# Activate the virtual environment
source fastenv/bin/activate

# Run the application in production mode
uvicorn app.main:app --workers 4
