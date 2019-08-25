How to start the application:

Install Docker:

    $ sudo apt install docker docker-compose

Enable docker.service on system startup 

    $ sudo systemctl enable docker

Launch Docker (in project directory):

    $ docker-compose up

This will bring both the application and the DB server up.
To launch it in the background, add a `-d` flag:

    $ docker-compose up -d

To create necessary tables in database in your favorite browser go to the page:
<http://192.168.5.14:8080/reset> 

The app will be running on <http://localhost:8080/>

## Debugging

To open a shell inside the container (replacing `task2_*` with your folder name):

    $ docker exec -it task2_web_1 bash

To run tests (replacing `task2_*` with your folder name):

    $ docker exec -it -w /code task2_web_1 python test.py

To reset the DB (remove all data):

    URL: <http://localhost:8080/reset>

To rebuild the container:

    $ docker-compose build
