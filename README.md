# GitHub Actions Templater Action
This is intended to take a workflow specification file (like this example) and workflow templates and generate GitHub Actions workflows.

The example-workflow should have the majority of options excercised and is a good example for how this all works. It starts with the simplest example and adds features step by step.

This action takes the following environment variabels (listed with their defaults):
  'TEMPLATE_LOCATION' defaults to: './tmp/template/'
  'DEFAULTS_FILE' defaults to: './tmp/defaults.yml'
  'WORKFLOWS_FILE' defaults to: './.github/workflows.yml'
  'OUTPUT_LOCATION' defaults to: './.github/workflows/'
