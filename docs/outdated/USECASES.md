# Usecases

## Breba Docs Intentions

As a software developer, I want to make sure that my documentation stays up to date.
Since correct documentation means the user can follow the steps described, Breba Docs
assumes the role of a user reading the documentation to complete own goals.

## Check Github docs

README.md and other files may have instructions for different feature and capabilities of the software. 
I want to make sure that the instructions provided in these files are correct and verified.

For example, I want to make sure the developer setup is correct and verified so that new team members can join seemlessly.

I want to provide my github repo and Breba Docs will read my README.md file.
It will identify the different goals mentioned in the readme file and execute them given the instructions provided.

I want to verify docs when there are changes to the repo. This can be done via Github Actions.
I want to verify docs before a PR is merged. This is done via PR checks.

### What does it mean to verify docs?

To verify docs Breba Docs will identify files, within files identify goals, look for instructions and execute them, and
then report on errors or warnings for each goal


### Reporting errors

I want to know when there are issues with my documentation. Breba Docs will submit pull requests fixing the issues from
the report of errors if it can modify the documentation, in such a way that makes verification pass.

## Verify public APIs

When I document public features of my software, I want to verify that they work as documented.
Side quest, find new and missing features and verify them


CLI
breba-docs new --name "My Project"
Creates a new project in the current directory.
Project has:
1. a data directory
2. config.yaml
3. a "prompts" directory that contains prompts

From inside the directory, you can run:
breba-docs run

This will execute "breba_docs.cli:run"

config.yaml
models: {model_id: {type: openai, name: gpt-4o, api_key: abc, temperature: 0.0, ...other_model_options}}


runner: 
{model: references created model, 
steps: {Goal: "Clone repo", "