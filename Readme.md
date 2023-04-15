# Demo app for the Invisible Screen


## What is the invisible screen?

It is an e-paper smart screen with an open platform so everybody can build apps for it. 

It is a great way to display information that you don't want to be distracted by.

Check it out here: https://shop.invisible-computers.com/products/invisible-calendar

## Where can I find documentation for building an app for the invisible screen?

Click here: [HowToBuildAnApp.md](HowToBuildAnApp.md)!


## What does this demo app do?

It pulls images from lorem picsum and displays them on the e-paper screen.
To show how users can change app settings, the user can configure whether the images should be displayed horizontally or vertically.

## How do I run this demo app?

1. Clone this repo
2. Install Poetry [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)
3. Tell poetry to use python 3.11: `poetry env use python3.11`
4. Install dependencies: `poetry install`
5. Setup the environment variables: `source setup_local_env.sh`
6. Launch the docker container with postgres: `docker-compose up -d`
7. Switch into the src directory: `cd src`
7. Run the django app: `poetry run python manage.py runserver`