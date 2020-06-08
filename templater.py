#!/usr/bin/env python3
from collections.abc import Mapping

from jinja2 import Environment, FileSystemLoader, Template
import yaml
import re
from os import path, getenv

template_location = getenv('TEMPLATE_LOCATION', './tmp/template/')
defaults_file = getenv('DEFAULTS_FILE', './tmp/defaults.yml')
workflow_spec_file = getenv('WORKFLOWS_FILE', './.github/workflows.yml')
output_location = getenv('OUTPUT_LOCATION', './.github/workflows/')

file_loader = FileSystemLoader(template_location)
env = Environment(loader=file_loader,
                  trim_blocks=True,
                  lstrip_blocks=True,
                  variable_start_string='{*',
                  variable_end_string='*}')


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

def build_custom_step_block(blocks, workflow_args):
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

def build_job_block(jobs, workflow_args):
    rendered_template = ''
    for job in jobs:
        if 'template_args' not in job.keys():
            job['template_args'] = []
        if 'type' in job.keys() and job['type'] == 'custom':
            rendered_steps = build_custom_step_block(job['blocks'], workflow_args)
        else:
            steps_template = env.get_template('/job/' + job['template'] + '.j2')
            rendered_steps = steps_template.render(job=job, args=workflow_args)
        job_template = env.get_template('/job/base.j2')
        rendered_template += job_template.render(job=job,rendered_steps=rendered_steps, args=workflow_args)
    return rendered_template.strip("\n")

def write_workflow(workflow, trigger_block, job_block):
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

def main():
    workflow_config = load_config(workflow_spec_file)
    
    if 'parameters' in workflow_config.keys():
        repo_args = workflow_config['parameters']
    else:
        repo_args = {}

    workflow_args = WorkflowArgs(load_config(defaults_file), repo_args)
    workflows = workflow_config['workflows']

    for workflow in workflows:
        trigger_block = build_trigger_block(workflow['triggers'])
        job_block = build_job_block(workflow['jobs'], workflow_args)
        write_workflow(workflow, trigger_block, job_block)

if __name__ == "__main__":
    main()
