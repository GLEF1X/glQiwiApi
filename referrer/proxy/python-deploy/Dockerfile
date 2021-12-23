# `python-base` sets up all our shared environment variables
FROM python:3.9-slim-bullseye as python-base


ENV PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    POETRY_VERSION=1.1.12 \
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    \
    # paths
    # this is where our requirements + virtual environment will live
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"\
    PYTHONUNBUFFERED=1



# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# `builder-base` stage is used to build deps + create our virtual environment
FROM python-base as builder-base
RUN apt-get -y update \
    && apt-get --no-install-recommends install -y \
        # deps for installing poetry
        curl \
        # deps for building python deps
        build-essential  \
        git && apt-get clean \ && rm -rf /var/lib/apt/lists/*

# istall poetry - respects $POETRY_VERSION & $POETRY_HOME
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# update poetry and install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry self update && poetry install --no-dev


# Прод-образ, куда копируются все собранные ранее зависимости
FROM builder-base as production
# create the node user
RUN groupadd --gid 2000 node \
  && useradd --uid 2000 --gid node --shell /bin/bash --create-home node
WORKDIR $PYSETUP_PATH
# copy in our built poetry + venv
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# quicker install as runtime deps are already installed
RUN poetry install

# chown all the files to the app user

ENV WORKDIR=/src
WORKDIR $WORKDIR
ENV PATH="/opt/venv/bin:$PATH"
COPY . $WORKDIR

RUN chown -R node:node $WORKDIR
USER 2000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5000 --workers ${GUNICORN_WORKERS} -k uvicorn.workers.UvicornWorker app:app"]

