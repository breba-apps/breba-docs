# Breba Docs

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
breba_docs
```

Then you will need to provide location of a documentation file. 
For example: `breba_docs/sample_doc.md`

The software will then analyze the documentation and run the commands found in the documentation
inside a docker container with python installed.

The AI will then provide feedback regarding how it was able to follow the instructions.

## Contributing
For contributing to the project, please refer to [Contribution Guide](docs/CONTRIBUTING.md). 