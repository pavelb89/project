import unittest
from contextlib import contextmanager
from datetime import datetime, date

from giftshop.app import app, db, models


class MyTestCase(unittest.TestCase):
    def setUp(self):
        # Reset the DB with every test
        with app.app_context():
            models.reset_db()

        ctx = app.app_context().__enter__()
        self.addCleanup(ctx.__exit__, None, None, None)

    # Test models

    def test_input_citizen_from_json(self):
        """ Test citizen JSON """
        # Incoming data
        json_data = {
            "citizen_id": 1,
            "town": "Москва",
            "street": "Льва Толстого",
            "building": "16к7стр5",
            "apartment": 7,
            "name": "Иванов Иван Иванович",
            "birth_date": "26.12.1986",
            "gender": "male",
            "relatives": [2]
        }

        # Create a Citizen from JSON
        imp = models.Import()
        citizen = models.Citizen(
            # Bind to the import object
            import_rel=imp,
            # Parse JSON data
            **json_data
        )

        # Make sure it all worked
        self.assertEqual(citizen.citizen_id, 1)
        self.assertEqual(citizen.town, 'Москва')
        self.assertEqual(citizen.relatives, [2])

        # Check age
        self.assertEqual(citizen.get_age(date(1987, 12, 25)), 0)
        self.assertEqual(citizen.get_age(date(1987, 12, 26)), 1)
        self.assertEqual(citizen.get_age(date(2006, 12, 26)), 20)

        # Save the citizen to the DB
        # `Import` object gets saved automatically
        ssn = db.session
        ssn.add(citizen)
        ssn.commit()

    def test_validation(self):
        """ Test if model validation works. """
        def test(**invalid_fields):
            with self.assertRaises(AssertionError):
                c = models.Citizen(**{'relatives': [], **invalid_fields})

        # Must throw errors in every case
        test(citizen_id=-1, )
        test(apartment='WRONG-STRING')
        test(town='', )
        test(street='', )
        test(building='', )
        test(name=None, )
        test(birth_date='WRONG-STRING')
        test(birth_date='31.02.2019')
        test(relatives=['a'])

    def test_set_relatives(self):
        """ Test Citizen.set_relatives() """
        ssn = db.session

        # Generate a bunch of people
        mother = self._create_citizen(1, [2, 10, 11])
        father = self._create_citizen(2, [1, 10, 11])
        mothers_sister = self._create_citizen(3, [1])

        son = self._create_citizen(10, [1, 2, 11, 20])
        daughter = self._create_citizen(11, [1, 2, 10])

        sons_girlfriend = self._create_citizen(20, [10])
        daughters_boyfriend = self._create_citizen(21, [11])

        forever_alone = self._create_citizen(30, [])
        stranger_girl = self._create_citizen(31, [])

        # Add all of them to the import
        imp = models.Import(citizens=[
            mother, father, mothers_sister,
            son, daughter,
            sons_girlfriend, daughters_boyfriend,
            forever_alone, stranger_girl
        ])

        # Save all of them
        ssn.add(imp)
        ssn.commit()

        # Now, divorce the family: mother has no husband anymore
        mother.relatives = [son.citizen_id, daughter.citizen_id]  # no more husband
        # Disappeared from relationships
        self.assertNotIn(father.citizen_id, mother.relatives)
        self.assertNotIn(mother.citizen_id, father.relatives)

        # Now, kill the son
        son.relatives = []
        # Disappeared from other relationships
        self.assertNotIn(son.citizen_id, father.relatives)
        self.assertNotIn(son.citizen_id, mother.relatives)
        self.assertNotIn(son.citizen_id, sons_girlfriend.relatives)
        self.assertNotIn(son.citizen_id, daughter.relatives)

        # The son was not dead. He ran away and married `stranger_girl`
        son.relatives = [stranger_girl.citizen_id]
        self.assertEqual(son.relatives, [stranger_girl.citizen_id])
        self.assertEqual(stranger_girl.relatives, [son.citizen_id])

        # The son has secretly contacted his sister
        son.relatives = [stranger_girl.citizen_id, daughter.citizen_id]
        self.assertIn(daughter.citizen_id, son.relatives)
        self.assertIn(son.citizen_id, daughter.relatives)

    def _create_citizen(self, citizen_id, relatives):
        """ Helper to create a citizen """
        return models.Citizen(
            citizen_id=citizen_id,
            town='a', street='b', building='c', apartment=1, name='e', birth_date='01.01.1970',
            gender='male', relatives=relatives
        )

    # Test API

    # Sample data
    sample_citizen = dict(citizen_id=1, town="M", street="S", building="B", apartment=1,
                          name="N", birth_date="26.12.1986", gender="male", relatives=[])
    sample_citizens = [
        {**sample_citizen, 'citizen_id': 1, 'name': 'A', 'relatives': [2, 3]},
        {**sample_citizen, 'citizen_id': 2, 'name': 'B', 'relatives': [1]},
        {**sample_citizen, 'citizen_id': 3, 'name': 'C', 'relatives': [1]},
        {**sample_citizen, 'citizen_id': 4, 'name': 'D', 'relatives': []},
        {**sample_citizen, 'citizen_id': 5, 'name': 'E', 'relatives': []},
    ]

    sample_citizens_invalid = [
        {**sample_citizen, 'citizen_id': 1, 'name': 'A', 'relatives': [3]},
        {**sample_citizen, 'citizen_id': 2, 'name': 'B', 'relatives': [2]},
        ]

    # Sample data from TASK.PDF
    sample_TASK_PDF = input_json = {
        "citizens": [
            {
                "citizen_id": 1,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Иван Иванович",
                "birth_date": "26.12.1986",
                "gender": "male",
                "relatives": [2, 3]  # id родственников
            },
            {
                "citizen_id": 2,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Сергей Иванович",
                "birth_date": "01.04.1997",
                "gender": "male",
                "relatives": [1]  # id родственников
            },
            {
                "citizen_id": 3,
                "town": "Санкт-Петербург",
                "street": "Иосифа Бродского",
                "building": "2",
                "apartment": 11,
                "name": "Романова Мария Леонидовна",
                "birth_date": "23.11.1986",
                "gender": "female",
                "relatives": [1]
            },
        ]
    }

    def test_api_imports(self):
        """ Test loading data into the /import API """
        ssn = db.session

        # Test: post invalid data
        with self.client() as c:
            rv = c.post('/imports', json={})
            self.assertEqual(rv.status, '400 BAD REQUEST')  # error
            self.assertIn('error', rv.get_json())

        # Test: post sample citizen
        valid_citizen = self.sample_citizen
        with self.client() as c:
            # Post, make sure no error
            rv = c.post('/imports', json={'citizens': [valid_citizen]})
            self.assertEqual(rv.status, '201 CREATED')  # must return code 201
            self.assertEqual(rv.get_json(), {'data': {'import_id': 1}})

            # See that it's been saved
            self.assertEqual(ssn.query(models.Citizen).count(), 1)

        # Test unique citizens ids and relatives
        citizens = self.sample_citizens_invalid
        with self.client() as c:
            rv = c.post('/imports', json={'citizens': citizens})
            self.assertEqual(rv.status, '400 BAD REQUEST')  # must return code 400

        # Test: unknown fields: must return code 400
        invalid_citizen = {**self.sample_citizen, 'UNKNOWN-FIELD': ''}
        with self.client() as c:
            rv = c.post('/imports', json={'citizens': [invalid_citizen]})
            self.assertEqual(rv.status, '400 BAD REQUEST')  # must return code 400

        # Test: validation
        def test_invalid_citizen(**invalid_fields):
            invalid_citizen = {**self.sample_citizen, **invalid_fields}
            with self.client() as c:
                rv = c.post('/imports', json={'citizens': [invalid_citizen]})
                self.assertEqual(rv.status_code, 400)

        test_invalid_citizen(citizen_id=-1)
        test_invalid_citizen(apartment=-1)
        test_invalid_citizen(town='')
        test_invalid_citizen(street='')
        test_invalid_citizen(building='')
        test_invalid_citizen(name='')
        test_invalid_citizen(birth_date='NOT-DATE-FORMAT')  # bad date format
        test_invalid_citizen(birth_date='31.02.2019')  # bad date
        test_invalid_citizen(relatives=['a', 'b', 'c'])  # bad relatives list

        # Test: many citizens
        citizens = self.sample_citizens
        with self.client() as c:
            rv = c.post('/imports', json={'citizens': citizens})
            self.assertEqual(rv.status_code, 201)  # must return code 201
            import_id = 2  # this is the import id we expect
            self.assertEqual(rv.get_json(), {'data': {'import_id': import_id}})

        # Test: TASK.PDF
        # Upload the very JSON from the document
        input_json = self.sample_TASK_PDF
        with self.client() as c:
            rv = c.post('/imports', json=input_json).get_json()
            self.assertEqual(rv['data']['import_id'], 3)

    def test_api_patch_citizen(self):
        """ Test: PATCH /imports/$import_id/citizens/$citizen_id """
        with self.client() as c:
            # Create citizens
            rv = c.post('/imports', json={'citizens': self.sample_citizens}).get_json()
            import_id = rv['data']['import_id']

            # Patch citizen
            citizen_id = 1
            rv = c.patch(f'/imports/{import_id}/citizens/{citizen_id}', json=dict(name='Z')).get_json()
            self.assertEqual(rv['data']['name'], 'Z')

            # Patch citizen: empty values
            rv = c.patch(f'/imports/{import_id}/citizens/{citizen_id}', json=dict())
            self.assertEqual(rv.status_code, 400)

            # Patch citizen: null values
            rv = c.patch(f'/imports/{import_id}/citizens/{citizen_id}', json=dict(name=None))
            self.assertEqual(rv.status_code, 400)

            # Patch citizen: relatives
            # Remove: 3, add:
            rv = c.patch(f'/imports/{import_id}/citizens/{citizen_id}',
                         json=dict(relatives=[2, 5])).get_json()
            self.assertEqual(rv['data']['relatives'], [2, 5])

            self.assertEqual(self.getCitizen(import_id, 1).relatives, [2, 5])  # changed
            self.assertEqual(self.getCitizen(import_id, 2).relatives, [1])  # 1 remains
            self.assertEqual(self.getCitizen(import_id, 3).relatives, [])  # 1 removed
            self.assertEqual(self.getCitizen(import_id, 5).relatives, [1])  # 1 added

    def test_api_get_import_citizens(self):
        """ Test: GET /imports/$import_id/citizens """
        with self.client() as c:
            # Create citizens
            rv = c.post('/imports', json={'citizens': self.sample_citizens}).get_json()
            import_id = rv['data']['import_id']

            # Load citizens
            rv = c.get(f'/imports/{import_id}/citizens').get_json()
            self.assertIn('data', rv)
            self.assertEqual(len(rv['data']), len(self.sample_citizens))
            self.assertEqual(rv['data'][0], self.sample_citizens[0])
            self.assertEqual(rv['data'], self.sample_citizens)

    def test_api_get_citizen_birthdays(self):
        """ Test: /imports/<int:import_id>/citizens/birthdays """
        with self.client() as c:
            # Create citizens
            rv = c.post('/imports', json=self.sample_TASK_PDF).get_json()
            import_id = rv['data']['import_id']

            # Test result
            rv = c.get(f'/imports/{import_id}/citizens/birthdays').get_json()
            self.assertEqual(rv, {
                # Expected output
                "data": {
                    "1": [],
                    "2": [],
                    "3": [],
                    "4": [{
                        "citizen_id": 1,
                        "presents": 1,
                    }],
                    "5": [],
                    "6": [],
                    "7": [],
                    "8": [],
                    "9": [],
                    "10": [],
                    "11": [{
                        "citizen_id": 1,
                        "presents": 1
                    }],
                    "12": [
                        {
                            "citizen_id": 2,
                            "presents": 1
                        },
                        {
                            "citizen_id": 3,
                            "presents": 1
                        }
                    ]}})

    def test_api_get_age_statistics(self):
        """ Test: /imports/<int:import_id>/towns/stat/percentile/age """
        with self.client() as c:
            # Create citizens
            rv = c.post('/imports', json=self.sample_TASK_PDF).get_json()
            import_id = rv['data']['import_id']

            # Test result
            rv = c.get(f'/imports/{import_id}/towns/stat/percentile/age').get_json()
            self.assertEqual(rv, {
                "data": [
                    {
                        "town": "Москва",
                        "p50": 27.0,
                        "p75": 29.5,
                        "p99": 31.9
                    },
                    {
                        "town": "Санкт-Петербург",
                        "p50": 32.0,
                        "p75": 32.0,
                        "p99": 32.0
                    }
                ]
            })

    @contextmanager
    def client(self):
        """ Get a client for testing the Flask application """
        app.testing = True
        client = app.test_client()

        with app.app_context():
            yield client

    def getCitizen(self, import_id, citizen_id, ssn=None):
        """ Load a citizen from the DB """
        if not ssn:
            ssn = db.session
        return ssn.query(models.Citizen).filter_by(import_id=import_id, citizen_id=citizen_id).one()


if __name__ == '__main__':
    unittest.main()
