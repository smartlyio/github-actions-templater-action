FROM python:3.8-alpine

LABEL version="1.0.0"
LABEL repository="https://github.com/smartlyio/github-actions-templater-action"
LABEL homepage="https://github.com/smartlyio/github-actions-templater-action"

LABEL com.github.actions.name="Build GitHub Action Workflows"
LABEL com.github.actions.icon="package"

# User user that has the same uid as Github's virtual runner. This causes the generated files to have assumed
# permissions.
RUN adduser -S runner -u 1001
USER runner

WORKDIR /templater
COPY requirements.txt /templater/requirements.txt
RUN pip install -r /templater/requirements.txt

COPY templater.py /templater/templater.py

WORKDIR /github/workspace

CMD [ "python", "/templater/templater.py" ]
