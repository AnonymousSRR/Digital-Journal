#!/usr/bin/env bash

# Pin to supported Python version
pyenv install -s 3.11.9
pyenv global 3.11.9

# Proceed with your normal build
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
