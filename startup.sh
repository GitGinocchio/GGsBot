#!/bin/bash

if [ -d .git ] && [ 1 = "1" ]; then
    #git config --global credential.helper store
    #git config --global pull.ff only  # Imposta la strategia di merge predefinita a fast-forward only
    git pull
fi

if [ -f "/home/container/requirements.txt" ]; then
    pip install -U --prefix .local -r "/home/container/requirements.txt"
fi

# /usr/local/bin/python /home/container/main.py
