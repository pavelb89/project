Application layout:

    requirements.txt:
        The list of applications to be installed
    giftshop/__init__.py:
        A file required for Python to see `giftshop` as a package (to allow relative imports)
    giftshop/app.py:
        The application itself
    giftshop/app_config.py:
        Application configuration file
    giftshop/models.py:
        Database structure
    giftshop/json.py:
        Custom JSON encoder to make sure objects from the DB look good in JSON
    test.py:
        Unit-tests


How to run the application:

    $ export FLASK_APP=giftshop/app.py FLASK_ENV=development
    $ flask run

Open the page:
http://127.0.0.1:5000
