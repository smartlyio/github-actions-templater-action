# GitHub Actions Templater Action
This is intended to take a workflow specification file (like this example) and workflow templates and generate GitHub Actions workflows.

The example-workflow should have the majority of options excercised and is a good example for how this all works. It starts with the simplest example and adds features step by step.

## Environment variables

| Variable          | Required  | Default                 | Description
|-------------------|-----------|-------------------------|--------------------------------------------------------------|
| MODE              | no        | RENDER                  | The mode to run in, see explanation below.                   |
| TEMPLATE_LOCATION | no        | ./tmp/template/         | Directory to find the templates in.                          |
| DEFAULTS_FILE     | no        | ./tmp/defaults.yml      | The defaults file to use.                                    |
| WORKFLOWS_FILE    | no        | ./.github/workflows.yml | The workflows.yml file to use to generate workflows.         |
| OUTPUT_LOCATION   | no        | ./.github/workflows/    | The location to put the resultant workflow files in.         |

The working directory for the templater action is the checked out repository.

## Modes

The template renderer works in two modes. Both are required to be executed in the same workflow to get full functionality.

### GET_REF
In this mode, the renderer will read the template and find the relevant branch of the template repo to pull for templating.

The branch is determined as follows:
If a `template_ref` variable is specified in `parameters` section of the `workflows.yml`, that is used.
Failing that, a `template_ref` variable in the `defaults.yml` is used.
If that also doesn't exist, `master` is used.

The mode is placed as an output into an environment variable named `TEMPLATE_PULL_REF`.

This can be referred to in later steps with: 
  `ref: ${{ steps.<STEP_ID>.outputs.TEMPLATE_PULL_REF }}`

### RENDER
This mode renders the workflows specified in `workflows.yml` into functional GitHub Actions workflows.

## Usage example

The action is used as follows:

```yaml
- uses: smartlyio/github-actions-templater-action@v1
  env:
    MODE: GET_ENV
```
