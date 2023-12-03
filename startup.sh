#!/bin/bash

if [ -d .git ] && [ 1 = "1" ]; then
    #git config credential.helper store
    #git config pull.rebase false  # Imposta la strategia di merge predefinita a merge
    #git config pull.rebase true  # Imposta la strategia di merge predefinita a rebase
    #git config pull.ff only  # Imposta la strategia di merge predefinita a fast-forward only
    git pull
fi

if [ -f "/home/container/requirements.txt" ]; then
    pip install -U --prefix .local -r "/home/container/requirements.txt"
fi

# /usr/local/bin/python /home/container/main.py
