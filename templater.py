#!/usr/bin/env python3
from collections.abc import Mapping

from jinja2 import Environment, FileSystemLoader, Template
import click
import yaml

import re
from os import path, getenv

class WorkflowArgs(Mapping):

    def __init__(self, defaults, repo_args):
        self.__defaults = defaults
        self.__repo_args = repo_args
        self.__keys = set(self.__defaults) | set(self.__repo_args)

    def __contains__(self, name):
        return name in self.__keys

    def __getitem__(self, name):
        try:
            return self.__repo_args[name]
        except KeyError:
            return self.__defaults[name]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __iter__(self):
        for key in self.__keys:
            yield key

    def __len__(self):
        # Length of the union of all keys
        return len(self.__keys)


def load_config(config_file):
    """
    Loads the yaml config file specified in 'config_file' and process it as yaml.
    Returns processed config
    """
    config = []
    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.SafeLoader)
        except yaml.YAMLError as exc:
            print("Problem processing config!")
            print(exc)
            exit(1)
    return config

def build_trigger_block(triggers):
    rendered_template = yaml.dump(triggers)
    return rendered_template.strip("\n")


def build_custom_step_block(blocks, workflow_args, template_location, env):
    rendered_steps = ''
    for block in blocks:
        if block['type'] == 'import':
            if path.exists(template_location + '/' + block['template'] + '.j2'):
                steps_template = env.get_template('/' + block['template'] + '.j2')
            else:
                print('Template ' + template_location + '/' + block['template'] + '.j2 not found!')
                exit(1)
        elif block['type'] == 'raw':
            steps_template = Template(yaml.dump(block['steps']) + '\n')
        else:
            print("Not a supported block type: " + block['type'])
            exit(1)
        rendered_steps += steps_template.render(job=block, args=workflow_args)

    return rendered_steps


def build_job_block(jobs, workflow_args, template_location, env):
    rendered_template = ''
    for job in jobs:
        if 'template_args' not in job.keys():
            job['template_args'] = []
        if 'type' in job.keys() and job['type'] == 'custom':
            rendered_steps = build_custom_step_block(job['blocks'], workflow_args, template_location, env)
        else:
            steps_template = env.get_template('/job/' + job['template'] + '.j2')
            rendered_steps = steps_template.render(job=job, args=workflow_args)
        job_template = env.get_template('/job/base.j2')
        rendered_template += job_template.render(job=job,rendered_steps=rendered_steps, args=workflow_args)
    return rendered_template.strip("\n")


def write_workflow(workflow, trigger_block, job_block, output_location, env):
    base_template = env.get_template('base.j2')

    workflow['triggers'] = trigger_block
    workflow['jobs'] = job_block

    output = base_template.render(workflow=workflow)

    if 'file' in workflow.keys():
        out_file_name = workflow['file']
    else:
        out_file_name = workflow['name'].replace(' ','_').lower()
        out_file_name = re.sub(r'\W+', '', out_file_name) + '.yml'
    
    print('Writing ' + out_file_name)
    with open(output_location + out_file_name, 'w+') as f:
        f.write(output)

def output_template_ref(repo_args):
    pull_ref = 'master'
    if 'template_ref' in repo_args:
        pull_ref = repo_args['template_ref']
    # Check that the branch spec is correct as per spec
    # Using example found here: https://stackoverflow.com/questions/12093748/how-do-i-check-for-valid-git-branch-names
    check_pattern=r'^(?!.*/\.)(?!.*\.\.)(?!/)(?!.*//)(?!.*@\\{)(?!@$)(?!.*\\)[^\000-\037\177 ~^:?*[]?/?[^\000-\037\177 ~^:?*[]+(?<!\.lock)(?<!/)(?<!\.)$'
    if not re.match(check_pattern, pull_ref):
        print("Invalid branch name given: " + pull_ref)
        exit(1)
    print("::set-env name=TEMPLATE_PULL_REF::" + pull_ref)


@click.command()
@click.option('--mode', envvar='MODE', type=click.Choice(['RENDER', 'GET_REF'], case_sensitive=False),
              default='RENDER',
              help="Mode to run in. In 'get_ref' mode, will output template ref that needs to be fetched." )
@click.option('--template_location', envvar='TEMPLATE_LOCATION', type=str,
              default='./tmp/template/', help='Look for templates in this directory')
@click.option('--defaults_file', envvar='DEFAULTS_FILE', type=str,
              default='./tmp/defaults.yml', help='Location of the defaults file')
@click.option('--workflow_spec_file', envvar='WORKFLOWS_FILE', type=str,
              default='./.github/workflows.yml', help='Location of the workflow spec file')
@click.option('--output_location', envvar='OUTPUT_LOCATION', type=str,
              default='./.github/workflows/', help='Where to put output workflows')
def main(mode, template_location, defaults_file, workflow_spec_file, output_location):
    workflow_config = load_config(workflow_spec_file)
    
    if 'parameters' in workflow_config.keys():
        repo_args = workflow_config['parameters']
    else:
        repo_args = {}

    workflow_args = WorkflowArgs(load_config(defaults_file), repo_args)
    workflows = workflow_config['workflows']

    if mode == 'RENDER':
        file_loader = FileSystemLoader(template_location)
        env = Environment(loader=file_loader,
                      trim_blocks=True,
                      lstrip_blocks=True,
                      variable_start_string='{*',
                      variable_end_string='*}')

        for workflow in workflows:
            trigger_block = build_trigger_block(workflow['triggers'])
            job_block = build_job_block(workflow['jobs'], workflow_args, template_location, env)
            write_workflow(workflow, trigger_block, job_block, output_location, env)

    elif mode == 'GET_REF':
        output_template_ref(repo_args)

    else:
        print("Unknown mode! " + mode)
        exit(1)


if __name__ == "__main__":
    main()
