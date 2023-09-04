REPOSITORY := llama
include ~/.nexus_auth

build:
	docker build --network=host \
	-f docker/Dockerfile \
	--build-arg="NEXUS_USER=${NEXUS_USER}" \
	--build-arg="NEXUS_PASS=${NEXUS_PASS}" \
	. -t $(REPOSITORY)

run: build up

up: 
	docker compose up -d  --remove-orphans
	docker compose logs -f 

down:
	docker compose down

debug:
	docker compose run -it --entrypoint bash datastream

push: build
	docker tag $(REPOSITORY):latest 10.252.1.0:1880/llama:latest
	docker push 10.252.1.0:1880/llama:latest

pgadmin:
	docker compose run pgadmin
