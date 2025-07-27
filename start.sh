#!/usr/bin/env bash
# Start the application
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT 