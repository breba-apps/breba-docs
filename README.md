# Breba Docs &middot; [![PyPI version](https://img.shields.io/pypi/v/breba-docs.svg)](https://pypi.org/project/breba-docs/)

_AI documentation validator_ 

[![workflow](https://github.com/breba-apps/breba-docs/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/breba-apps/breba-docs/actions/workflows/test.yaml?query=branch%3Amain)

## Features
Scans your documentation file and executes commands in the documentation
to make sure that it is possible to follow the documentation.

## Getting Started

### Prerequisites
Docker engine needs to be installed and running. Use docker installation instructions for your system.

Get an OpenAI API Key and set environment variable like this:
```bash
export OPENAI_API_KEY=[your_open_ai_api_key]
```

### Install and Run
To install and run breba-docs, run the following commands:

```bash
pip install breba-docs
breba-docs new sample_proj
cd sample_proj
breba-docs run
```

Then you will need to provide location of a documentation file. 
For example: `sample_project/sample.md`

The software will then analyze the documentation and run the commands found in the documentation
inside a docker container with python installed.

The AI will then provide feedback regarding how it was able to follow the instructions.

## Features

- **Create a New Project:**  
  Run `breba-docs new` to set up a new project with:
  - `data` directory
  - `prompts` directory
  - `config.yaml` file containing project and model configuration

- **Run the Project:**  
  Run `breba-docs run` to load and display your project's configuration.

  When providing a path to file, that file will be copied to the `data` directory.

  When using a github url, the repo will be cloned inside the `data` directory.

  The software will then analyze the documentation and run the commands found in the documentation

  Commands will be run inside a docker container with python installed.

  Commands to fix the documentation will run against the documentation in the `data` directory.

## Contributing
For contributing to the project, please refer to [Contribution Guide](docs/CONTRIBUTING.md). 