REPOSITORY := llama

build:
	docker build -f docker/Dockerfile . -t $(REPOSITORY)

run: build
	docker compose up

debug:
	docker compose run -it --entrypoint bash $(REPOSITORY)-api

