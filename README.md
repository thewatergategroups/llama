#### Setup Process
1. Create .env file locally and add relevant secrets to it 
```bash
cat << EOF > ./.env
API_KEY=<alpaca api key>
API_ENDPOINT=https://paper-api.alpaca.markets
SECRET_KEY=<alpaca secret key>
PGDATABASE=postgres
PGHOST=localhost
PGPASSWORD=postgres
PGUSER=postgres
DB_SCHEMA=llama
DEV_MODE=true
EOF
```
2. add the pypi repository creds to `~/pypi_creds`
```bash
cat << EOF > ~/pypi_creds
PYPI_USER=admin
PYPI_PASS=admin
EOF
```
3. Set up poetry deps
```bash
poetry config http-basic.kube <PYPI_USER> <PYPI_PASS>
poetry config virtualenvs.in-project true
``` 
4. contact `ciaranmckey@gmail.com` about giving you access to relevant repositories
5. Connect to the wireguard VPN
6. run `make build` to build the docker image

#### Differnet Modes 
##### Bring up all services
1. run `make up`
    - This will bring up all services and the API docs page in your browser
2. run `make up PGADMIN=true` 
    - this will start up all services, as well as pgadmin. The API docs and PGAdmin will be  opened in the browser.

2. run `make up DOCS=false` 
    - this will start up all services. API docs WONT be opened

##### Bring up pgadmin separately
1. run `make pgadmin`
    - this will bring up pgadmin and the database. It will open the browser on the pgadmin page 

##### Run a backtest based in a json definition
1. run `make backtest`
    - This will read out of the local file `backtests.json` and run backtests with the specified strategies, conditions against the specified symbols

##### Run random debugging functions
1. run `make debug`
    - this will run the `debug` function found in the `entrypoints.py` file. Modify this function to modify what this command does

##### Open a bash shell in a llama container
1. run `make shell`
    - this will open up a terminal for you inside the docker container

##### Bring down all services
1. run `make down`

