#! /bin/bash 

if [[ $DEV_MODE = "true" ]]; then
    echo installing dev deps
    poetry install
else
    echo installing prod deps
    poetry install --only main
fi