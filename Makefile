REPOSITORY := llama
include ~/pypi_creds


build:
	docker build --network=host \
	-f docker/Dockerfile \
	--build-arg="PYPI_USER=${PYPI_USER}" \
	--build-arg="PYPI_PASS=${PYPI_PASS}" \
	. -t $(REPOSITORY)


run: build up

api:
	docker compose run api 

up: 
	docker compose --profile trader --profile db up -d --remove-orphans
	docker compose --profile trader logs -f 

kill:
	docker kill llama-api-1
	docker kill llama-tradestream-1
	docker kill llama-datastream-1

down: 
	docker compose --profile trader --profile db down


push: build
	docker tag $(REPOSITORY):latest ghcr.io/1ndistinct/llama:latest
	docker push  ghcr.io/1ndistinct/llama:latest

pgadmin:
	docker compose run pgadmin


template:
	if [ ! -f secret_vals.yaml ]; then echo "secrets: {}" > secret_vals.yaml; fi
	helm template ./helm/${PROJECT}-local -f secret_vals.yaml --debug > template.yaml
