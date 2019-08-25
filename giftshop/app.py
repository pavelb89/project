# Environment packages
import time
from datetime import date
from sqlalchemy.orm import exc as sa_exc
from flask import Flask, request, jsonify
from collections import Counter
from numpy import array, percentile


# Application packages
from . import models, json

# Init Flask
app = Flask(__name__)
app.config.from_pyfile('app_config.py')
app.json_encoder = json.JSONEncoder

# Init Database
db = models.db
db.init_app(app)

# Init views


# ### Views for testing
@app.route('/')
def api_index():
    return 'Hi!'


@app.route('/reset')
def api_reset_db():
    """ Reset the database: recreate all tables """
    models.reset_db()
    return 'Database is reset'


@app.route('/sleep/<int:n>')
def api_sleep(n=10):
    """ A blocking view to test parallel requests """
    time.sleep(n)
    return f'Slept for {n} seconds'


@app.route('/json')
def api_json():
    """ Example of a JSON endpoint """
    ssn = db.session

    # Create a new import
    imp = models.Import()

    # Create a Citizen
    citizen = models.Citizen(
        import_rel=imp,  # bind to the Import
        citizen_id=1,
        town='a', street='b', building='c', apartment=2, name='e', birth_date='31.08.2019', gender='male',
        relatives=[2],
    )

    # Save to the DB
    # At this step, objects get their IDs
    ssn.add(imp)
    ssn.add(citizen)
    ssn.commit()

    # Return the data. Make sure it looks good in JSON
    return jsonify({
        'import': imp,
        'citizen': citizen
    })


# ### Views for import
@app.route('/imports', methods=['POST'])
def api_imports():
    ssn = db.session

    # Get data; fail on any error
    try:
        citizens = request.get_json()['citizens']
    except Exception as e:
        return json.json_error(e), 400

    # Prepare an import, create citizens
    # Validate citizen_id and relatives
    # 1) citizen_id should be unique in every import
    # 2) set of relatives should <= set of citizen_id
    imp = models.Import()
    relatives_ids = set()
    citizen_ids = set()
    for citizen in citizens:
        try:
            current_id = int(citizen['citizen_id'])
            if current_id not in citizen_ids:
                citizen_ids.add(current_id)
                relatives_ids = relatives_ids.union(set(map(int, citizen['relatives'])))
            else:
                return json.json_error(AssertionError), 400
            ssn.add(models.Citizen(import_rel=imp, **citizen))

        # the model would throw a TypeError when an invalid field name is given
        except TypeError as e:
            return json.json_error(e), 400
        except KeyError as e:
            return json.json_error(e), 400
        except ValueError as e:
            return json.json_error(e), 400
        # validation errors are reported as AssertionError
        except AssertionError as e:
            return json.json_error(e), 400

    if relatives_ids - citizen_ids != set():
        return json.json_error(ValueError), 400

    # Save
    ssn.add(imp)
    ssn.commit()

    return {'data': {'import_id': imp.import_id}}, 201


@app.route('/imports/<int:import_id>/citizens/<int:citizen_id>', methods=['PATCH'])
def api_patch_citizen(import_id, citizen_id):
    ssn = db.session

    # Get data; fail on any error
    try:
        citizen_data = request.get_json()
        assert isinstance(citizen_data, dict) and len(citizen_data) != 0, 'No data sent'
        assert 'citizen_id' not in citizen_data, 'Cannot change citizen_id'
    except Exception as e:
        return json.json_error(e), 400

    # Load the citizen
    try:
        citizen = ssn.query(models.Citizen) \
            .filter_by(import_id=import_id, citizen_id=citizen_id) \
            .one()
    except sa_exc.NoResultFound as e:
        return json.json_error(e), 400

    # Modify the citizen
    for field_name, field_value in citizen_data.items():
        try:
            setattr(citizen, field_name, field_value)
        # Validation errors
        except AssertionError as e:
            return json.json_error(e), 400

    # Save
    ssn.add(citizen)
    ssn.commit()

    # Done
    return {
        'data': citizen
    }


def _load_all_citizens(ssn, import_id):
    """ Load all citizens from an Import identified by `import_id` """
    return ssn.query(models.Citizen) \
        .filter(models.Citizen.import_id == import_id) \
        .order_by(models.Citizen.citizen_id.asc()) \
        .all()


@app.route('/imports/<int:import_id>/citizens')
def api_load_import(import_id):
    ssn = db.session

    # Load citizens
    citizens = _load_all_citizens(ssn, import_id)

    # Return
    return {
        'data': citizens
    }


@app.route('/imports/<int:import_id>/citizens/birthdays')
def api_get_citizen_birthdays(import_id):
    ssn = db.session
    citizens = {citizen.citizen_id: citizen
                for citizen in _load_all_citizens(ssn, import_id)}

    info = {str(k): [] for k in range(1, 13)}
    for citizen_id, citizen in citizens.items():
        months = Counter([citizens[person].birth_date.month for person in citizen.relatives])
        for month in months:
            info[str(month)].append(
                {
                    'citizen_id': citizen_id,
                    'presents': months[month]
                }
            )
        months.clear()

    return {
        'data': info
    }


@app.route('/imports/<int:import_id>/towns/stat/percentile/age')
def api_get_age_statistics(import_id):
    ssn = db.session
    citizens = _load_all_citizens(ssn, import_id)

    towns = dict()
    for citizen in citizens:
        towns.setdefault(citizen.town, []).append(citizen.get_age(date.today()))

    data = []
    for town, values in towns.items():
        stat = percentile(array(values), q=[50, 75, 99], interpolation='linear')
        data.append(
            {
                'town': town,
                'p50': round(stat[0], 2),
                'p75': round(stat[1], 2),
                'p99': round(stat[2], 2)
            }
        )
    # raise NotImplementedError()
    return {
        'data': data
    }
