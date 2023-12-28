#! /bin/bash 
poetry config http-basic.kube $PYPI_USER $PYPI_PASS
if [[ $DEV_MODE = "true" ]]; then
    echo installing dev deps
    poetry install
else
    echo installing prod deps
    poetry install --only main
fi