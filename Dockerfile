FROM ghcr.io/thewatergategroups/ops:python311 AS requirements
ARG PYPI_USER
ARG PYPI_PASS
COPY pyproject.toml poetry.lock ./
RUN poetry config http-basic.kube $PYPI_USER $PYPI_PASS && poetry install --without dev

FROM requirements AS dev_requirements
    RUN poetry install --only dev


FROM ghcr.io/thewatergategroups/ops:python311 AS base
RUN groupadd app && useradd -g app --home-dir /app --create-home app
WORKDIR /app 
COPY  ./scripts/start.sh ./
COPY ./llama ./llama
RUN chown -R app /app && chmod -R 700 /app
ENTRYPOINT ["bash","start.sh"]


FROM base AS development
COPY --from=dev_requirements /usr /usr
COPY ./backtests.json ./

FROM base AS production
COPY --from=requirements /usr /usr
USER app
