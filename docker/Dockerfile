FROM base:py as requirements
COPY pyproject.toml poetry.lock ./scripts/build.sh ./
RUN bash ./build.sh 

from base:py
COPY --from=requirements /usr /usr
RUN groupadd app && useradd -g app --home-dir /app --create-home app
WORKDIR /app 
COPY  ./scripts/start.sh ./
COPY ./alpaca ./alpaca
RUN chown -R app /app && chmod -R 700 /app
USER app
ENTRYPOINT ["bash","start.sh"]
CMD ["python","-m","alpaca"]