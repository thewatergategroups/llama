REPOSITORY := alpaca

build:
	docker build -f docker/Dockerfile.python311 . -t base:py
	docker build -f docker/Dockerfile . -t $(REPOSITORY)

run: build
	docker compose up

debug:
	docker run -it --rm $(REPOSITORY) bash

