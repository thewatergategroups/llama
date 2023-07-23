FROM ghcr.io/1ndistinct/ops:python311 as requirements
COPY pyproject.toml poetry.lock ./scripts/build.sh ./
RUN bash ./build.sh 

FROM ghcr.io/1ndistinct/ops:python311
COPY --from=requirements /usr /usr
RUN groupadd app && useradd -g app --home-dir /app --create-home app
WORKDIR /app 
COPY  ./scripts/start.sh ./
COPY ./llama ./llama
RUN chown -R app /app && chmod -R 700 /app
# USER app ##disable for dev
# ENTRYPOINT ["bash","start.sh"]
CMD ["python","-m","llama"]