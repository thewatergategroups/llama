REPOSITORY := llama
include ~/.nexus_auth

build:
	docker build --network=host \
	-f docker/Dockerfile \
	--build-arg="NEXUS_USER=${NEXUS_USER}" \
	--build-arg="NEXUS_PASS=${NEXUS_PASS}" \
	. -t $(REPOSITORY)

run: build
	docker compose up

debug:
	docker compose run -it --entrypoint bash $(REPOSITORY)-api

push: build
	docker tag $(REPOSITORY):latest 10.252.1.0:1880/llama:latest
	docker push 10.252.1.0:1880/llama:latest