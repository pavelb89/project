import enum
from datetime import date
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey, ARRAY, UniqueConstraint
from sqlalchemy.orm import relationship, validates, object_session
from sqlalchemy.ext.mutable import MutableList

import re

db = SQLAlchemy()


class Gender(enum.Enum):
    male = 'male'
    female = 'female'


class Import(db.Model):
    """ Одна выгрузка """
    import_id = Column(Integer, primary_key=True, doc="Уникальный номер выгрузки")

    citizens = relationship('Citizen', back_populates='import_rel')

    def __json__(self):
        return {
            'import_id': self.import_id
        }


class Citizen(db.Model):
    """ Один житель """
    __tablename__ = 'citizens'
    __table_args__ = (
        # Every citizen_id is unique within an import
        UniqueConstraint('import_id', 'citizen_id'),
    )

    id = Column(Integer, primary_key=True, doc="Уникальный номер человека в нашей системе")
    import_id = Column(Integer, ForeignKey(Import.import_id), nullable=False, doc="Номер выгрузки")
    import_rel = relationship(Import, back_populates='citizens')


    # Incoming data
    citizen_id = Column(Integer, nullable=False, doc="Уникальный идентификатор жителя (уникальный в пределах одной выгрузки)")
    town = Column(String, nullable=False, doc="Название города")
    street = Column(String, nullable=False, doc="Название улицы")
    building = Column(String, nullable=False, doc="Номер дома, корпус и строение")
    apartment = Column(Integer, nullable=False, doc="Номер квартиры")
    name = Column(String, nullable=False, doc="Непустая строка")
    birth_date = Column(Date, nullable=False, doc="Дата рождения в формате (UTC)")
    gender = Column(Enum(Gender), nullable=False, doc="Пол")

    _relatives = Column(MutableList.as_mutable(ARRAY(Integer)), nullable=False, default=list,  # list of ids
                       doc="Ближайшие родственники, уникальные значения существующих citizen_id жителей из этой же выгрузки.")

    def __init__(self, relatives=(), **fields):
        """ Init method that supports `relatives` """
        super().__init__(**fields)
        self._relatives = relatives

    def __json__(self):
        """ Representation in JSON """
        return {
            'citizen_id': self.citizen_id,
            'town': self.town,
            'street': self.street,
            'building': self.building,
            'apartment': self.apartment,
            'name': self.name,
            'birth_date': self.birth_date,
            'gender': self.gender,
            'relatives': self.relatives,
        }

    def get_age(self, today: date.today()):
        """ Get age in years """
        age = today.year - self.birth_date.year
        if today.month < self.birth_date.month:
            age -= 1
        elif today.month == self.birth_date.month and today.day < self.birth_date.day:
            age -= 1
        return age

    @property
    def relatives(self):
        """ Get the list of relatives """
        return self._relatives

    @relatives.setter
    def relatives(self, relatives):
        """ Change the value of `relatives`

        This method would also update the lists of related citizens.
        Make sure to do `db.session.commit()` to save those changes to the DB
        """
        # Detect modifications: added, removed
        current_relatives = set(self._relatives)
        updated_relatives = set(relatives)

        # List of added, list of removed ids
        added_ids = updated_relatives - current_relatives
        removed_ids = current_relatives - updated_relatives

        if 0 and 'debug section':
            print(f'citizen_id: {self.citizen_id}')
            print(f'    current_relatives: {current_relatives}')
            print(f'    updated_relatives: {updated_relatives}')
            print(f'    added_ids: {added_ids}')
            print(f'    removed_ids: {removed_ids}')

        # Get the Session from ourselves
        ssn = object_session(self)

        # Find those added people and modify them
        added = ssn.query(Citizen).filter(
            # Find people in the same import
            Citizen.import_id == self.import_id,
            # Query by id
            Citizen.citizen_id.in_(added_ids)
        )

        for citizen in added:
            citizen._relatives.append(self.citizen_id)
            citizen._relatives = list(citizen._relatives)
            ssn.add(citizen)

        # Find those removed people and modify them
        removed = ssn.query(Citizen).filter(
            Citizen.import_id == self.import_id,
            Citizen.citizen_id.in_(removed_ids)
        )

        for citizen in removed:
            citizen._relatives.remove(self.citizen_id)
            citizen._relatives = list(citizen._relatives)
            ssn.add(citizen)

        # Finally, update ourselves
        self._relatives = list(updated_relatives)
        return self.relatives

    # Validators

    @validates('citizen_id')
    def validate_citizen_id(self, _key, value):
        return validate_positive_number(value)

    @validates('apartment')
    def validate_apartment(self, _key, value):
        return validate_positive_number(value)

    @validates('town')
    def validate_town(self, _key, value):
        return validate_nullable_alphanumeric(value)

    @validates('street')
    def validate_street(self, _key, value):
        return validate_nullable_alphanumeric(value)

    @validates('building')
    def validate_building(self, _key, value):
        return validate_nullable_alphanumeric(value)

    @validates('name')
    def validate_name(self, _key, value):
        assert isinstance(value, str) and value
        return value

    @validates('birth_date')
    def validate_birth_date(self, _key, value):
        # Convert date string to `date` object
        if isinstance(value, str):
            try:
                day, month, year = map(int, value.split('.'))
                value = date(year, month, day)
            except ValueError as e:
                raise AssertionError('Invalid date format') from e
        return value

    @validates('gender')
    def validate_gender(self, _key, value):
        assert value == Gender.male.name or value == Gender.female.name
        return value

    @validates('_relatives')
    def _validate_relatives(self, _key, values):
        # List of int
        assert all(isinstance(v, int) for v in values)
        return values


def reset_db():
    """ Reset the database: recreate all tables """
    db.reflect()
    db.drop_all()
    db.create_all()
    return 'Database is reset'


nonempty_alphanumeric_str = re.compile('[\w\d]')


def validate_positive_number(v):
    assert isinstance(v, int) and v >= 0
    return v


def validate_nullable_alphanumeric(v):
    # Regular Expression check: contains at least one letter/digit
    assert isinstance(v, str) and nonempty_alphanumeric_str.match(v)
    return v
