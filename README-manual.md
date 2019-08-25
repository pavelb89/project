How to start the application:

Create a Python virtualenv, and tell Git to ignore it:

    $ python3.7 -m virtualenv venv
    $ echo venv > .git/info/exclude

Activate a virtualenv

    $ . venv/bin/activate

Install some packages that we need:

    $ pip install -r requirements.txt
    
Run unit-tests:

    $ python test.py
    
Make sure your database URL is correct in `giftshop/app_config.py`.
Run the application on http://localhost:8080/

    $ flask run -h 0.0.0.0 -p 8080
