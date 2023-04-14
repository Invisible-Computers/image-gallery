FROM python:3.11
ENV PYTHONUNBUFFERED 1


RUN mkdir -p /home/docker/repo
WORKDIR /home/docker/repo

# install dependencies
RUN pip install "poetry==1.4.2"
ADD ./pyproject.toml /home/docker/repo/pyproject.toml
ADD ./poetry.lock /home/docker/repo/poetry.lock
RUN poetry config virtualenvs.create false && poetry install --without dev --no-interaction --no-ansi  --no-root

# Mount code
ADD . /home/docker/repo/

ENV DJANGO_SETTINGS_MODULE image_gallery.settings


CMD /home/docker/repo/boot.sh