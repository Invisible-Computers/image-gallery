#!/bin/sh
set -e

whoami
python /home/docker/repo/src/manage.py migrate --noinput
python /home/docker/repo/src/manage.py collectstatic --noinput
python /home/docker/repo/src/manage.py createcachetable

uwsgi --ini /home/docker/repo/uwsgi.ini
