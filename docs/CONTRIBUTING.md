# Contibution Guide

## Reporting an issue
Submit an issue to [https://github.com/breba-apps/breba-docs/issues](https://github.com/breba-apps/breba-docs/issues)

## Prerequisites for Developing
You will need python 3.12 or later to run the code.

### Install docker
Install docker on your system. See [docker installation instructions](https://docs.docker.com/get-docker/).

### Install poetry
Install poetry to manage dependencies. See [poetry installation instructions](https://python-poetry.org/docs/#installation)

## Developing

### Fork the repository and build docker image
Fork the repository. Then clone it to your local machine:
```shell
git clone https://github.com/breba-apps/you-username/breba-docs.git
```

### Configure OpenAI key
Create a `.env` file similar to `.env.sample`
```
BREBA_IMAGE=breba-image
OPENAI_API_KEY=
```
### Check docker setup
Docker should run without errors
```
docker ps
```

### Run the code
```shell
cd breba-docs
docker build -t breba-image .  
poetry install
poetry run breba_docs
```

### Run the tests
```shell
poetry run pytest
```

### Create a Pull Request
1. Make sure to run tests locally before creating a PR.
2. Then update docs relating to the change.
3. Then create the PR

