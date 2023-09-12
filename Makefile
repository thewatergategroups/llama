REPOSITORY := llama
include ~/.nexus_auth

build:
	docker build --network=host \
	-f docker/Dockerfile \
	--build-arg="NEXUS_USER=${NEXUS_USER}" \
	--build-arg="NEXUS_PASS=${NEXUS_PASS}" \
	. -t $(REPOSITORY)

run: build up

api:
	docker compose run api 

up: 
	docker compose --profile trader --profile db up -d --remove-orphans
	docker compose --profile trader logs -f 

down:
	docker kill llama-api-1
	docker kill llama-tradestream-1
	docker kill llama-datastream-1



debug:
	docker compose run -it --entrypoint bash datastream

push: build
	docker tag $(REPOSITORY):latest 10.252.1.0:1880/llama:latest
	docker push 10.252.1.0:1880/llama:latest

pgadmin:
	docker compose run pgadmin
