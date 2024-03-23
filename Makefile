REPOSITORY := llama
include ~/pypi_creds

build:
	docker build --network=host \
	-f docker/Dockerfile \
	--build-arg="PYPI_USER=${PYPI_USER}" \
	--build-arg="PYPI_PASS=${PYPI_PASS}" \
	. -t $(REPOSITORY)

debug:
	docker compose run --entrypoint bash api 

up: 
	docker compose up -d --remove-orphans
	docker compose logs -f 

down: 
	docker compose down

push: build
	docker tag $(REPOSITORY):latest ghcr.io/1ndistinct/llama:latest
	docker push  ghcr.io/1ndistinct/llama:latest

template:
	if [ ! -f secret_vals.yaml ]; then echo "secrets: {}" > secret_vals.yaml; fi
	helm template ./helm/${PROJECT}-local -f secret_vals.yaml --debug > template.yaml

