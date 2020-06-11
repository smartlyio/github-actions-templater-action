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


def no_duplicates_constructor(loader, node, deep=False):
    """Check for duplicate keys."""
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            msg = "Duplicate key {0} (overwrite existing value '{1}' with new value '{2}'"
            msg = msg.format(key, mapping[key], value_node)
            raise yaml.YAMLError(msg)
        value = loader.construct_object(value_node, deep=deep)
        mapping[key] = value
    return loader.construct_mapping(node, deep)


def construct_mapping(loader, node):
    loader.flatten_mapping(node)
    return object_pairs_hook(loader.construct_pairs(node))


class DupCheckLoader(yaml.Loader):
    """Local class to prevent pollution of global yaml.Loader."""
    pass

DupCheckLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                               no_duplicates_constructor)

def load_config(config_file):
    """
    Loads the yaml config file specified in 'config_file' and process it as yaml.
    Returns processed config
    """
    config = []

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=DupCheckLoader)
        except yaml.YAMLError as exc:
            print("Problem processing config!")
            print(exc)
            exit(1)
    return config


def build_trigger_block(triggers, template_location, env):
    rendered_triggers = ''
    for trigger in triggers:
        if trigger == 'template':
            trigger_template = env.get_template('trigger/' + triggers[trigger] + '.j2')
            rendered_triggers += trigger_template.render(trigger=trigger)
        else:
            rendered_triggers += yaml.dump({trigger : triggers[trigger]}, default_flow_style=False)
    return rendered_triggers.strip("\n")


def build_custom_step_block(blocks, workflow_args, template_location, env):
    rendered_steps = ''
    for block in blocks:
        if 'template' in block.keys():
            steps_template = env.get_template(block['template'] + '.j2')
        elif block['type'] == 'raw':
            steps_template = Template(yaml.dump(block['steps'], default_flow_style=False) + '\n')
        else:
            print("Not a supported block type: " + str(block))
            exit(1)
        rendered_steps += steps_template.render(job=block, args=workflow_args)

    return rendered_steps


def build_job_block(jobs, workflow_args, template_location, env):
    rendered_jobs = []
    for job in jobs:
        if 'template_args' not in job.keys():
            job['template_args'] = []
        if 'type' in job.keys() and job['type'] == 'custom':
            rendered_steps = build_custom_step_block(job['blocks'], workflow_args, template_location, env)
        elif 'template' in job.keys():
            steps_template = env.get_template('job/' + job['template'] + '.j2')
            rendered_steps = steps_template.render(job=job, args=workflow_args)
        else:
            print("Unknown job type: " + str(job))
            exit(1)
        job_template = env.get_template('job/base.j2')
        rendered_jobs.append(job_template.render(job=job, rendered_steps=rendered_steps, args=workflow_args))
    return rendered_jobs


def write_workflow(workflow, output_location, env, trigger_block=None, job_blocks=None, workflow_args=None):

    if 'template' in workflow.keys():
        base_template = env.get_template('workflow/' + workflow['template'] + '.j2')
    else:
        base_template = env.get_template('workflow/base.j2')
        workflow['triggers'] = trigger_block
        workflow['jobs'] = job_blocks

    output = base_template.render(workflow=workflow, args=workflow_args)

    if 'file' in workflow.keys():
        out_file_name = workflow['file']
    elif 'name' in workflow.keys():
        out_file_name = workflow['name'].replace(' ','_').lower()
        out_file_name = re.sub(r'\W+', '', out_file_name) + '.yml'
    elif 'template' in workflow.keys():
        out_file_name = workflow['template'].replace('/', '_') + '.yml'
    else:
        print("No way to determine a name for this workflow: " + str(workflow))

    
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

    if mode == 'RENDER':
        workflow_args = WorkflowArgs(load_config(defaults_file), repo_args)
        workflows = workflow_config['workflows']

        file_loader = FileSystemLoader(template_location)
        env = Environment(loader=file_loader,
                      trim_blocks=True,
                      lstrip_blocks=True,
                      variable_start_string='{*',
                      variable_end_string='*}')

        for workflow in workflows:
            if 'template' not in workflow.keys():
                trigger_block = build_trigger_block(workflow['triggers'], template_location, env)
                job_blocks = build_job_block(workflow['jobs'], workflow_args, template_location, env)
                write_workflow(workflow, output_location, env, 
                               trigger_block=trigger_block, job_blocks=job_blocks)
            else:
                write_workflow(workflow, output_location, env, workflow_args=workflow_args)

    elif mode == 'GET_REF':
        output_template_ref(repo_args)

    else:
        print("Unknown mode! " + mode)
        exit(1)


if __name__ == "__main__":
    main()
