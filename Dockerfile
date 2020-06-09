FROM python:3.8-alpine

LABEL version="1.0.0"
LABEL repository="https://github.com/smartlyio/github-actions-templater-action"
LABEL homepage="https://github.com/smartlyio/github-actions-templater-action"

LABEL com.github.actions.name="Build GitHub Action Workflows"
LABEL com.github.actions.icon="package"

WORKDIR /templater
COPY requirements.txt /templater/requirements.txt
RUN pip install -r /templater/requirements.txt

COPY templater.py /templater/templater.py

WORKDIR /github/workspace

CMD [ "python", "/templater/templater.py" ]
