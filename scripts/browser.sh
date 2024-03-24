#! /bin/bash

open_browser() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: open_browser <URL>"
        return 1
    fi

    xdg-open "$1" >/dev/null 2>&1
}

if [[ ${DOCS} != "false" ]]; 
then 
open_browser http://localhost:8000/docs
fi

if [[ ${PGADMIN} == "true" ]]; 
then 
open_browser http://localhost:8080
fi