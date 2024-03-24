REPOSITORY := llama
SHELL := /bin/bash
include ~/pypi_creds

build:
	docker build --network=host \
	-f docker/Dockerfile \
	--build-arg="PYPI_USER=${PYPI_USER}" \
	--build-arg="PYPI_PASS=${PYPI_PASS}" \
	. -t $(REPOSITORY)

debug:
	docker compose run --entrypoint "python -m llama debug" api 

backtest:
	docker compose run --entrypoint "python -m llama backtest" api 

shell:
	docker compose run --entrypoint bash api 

up: 
	docker compose up -d --remove-orphans
	if [ $(PGADMIN) == "true" ]; then docker compose --profile pgadmin up -d; fi
	echo "sleeping to allow services to start up..."
	sleep 15
	export PGADMIN=$(PGADMIN) && bash ./scripts/browser.sh
	docker compose logs -f 

pgadmin: 
	docker compose --profile pgadmin up -d
	echo "sleeping to allow services to start up..."
	sleep 15
	export PGADMIN=true && \
	export DOCS=false && \
	bash ./scripts/browser.sh

down: 
	docker compose --profile "*" down

push: build
	docker tag $(REPOSITORY):latest ghcr.io/1ndistinct/llama:latest
	docker push  ghcr.io/1ndistinct/llama:latest

template:
	if [ ! -f secret_vals.yaml ]; then echo "secrets: {}" > secret_vals.yaml; fi
	helm template ./helm/${PROJECT}-local -f secret_vals.yaml --debug > template.yaml

