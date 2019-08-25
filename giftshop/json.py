from logging import getLogger
from enum import Enum
from datetime import date

import flask.json

logger = getLogger(__name__)


class JSONEncoder(flask.json.JSONEncoder):
    """ Custom JSON encoder that handles additional types """
    def default(self, v):
        if hasattr(v, '__json__'):
            # Custom encoders
            return v.__json__()
        elif isinstance(v, date):
            # Dates
            return f'{v.day:02d}.{v.month:02d}.{v.year}'
        elif isinstance(v, Enum):
            return v.name
        elif isinstance(v, set):
            return list(v)
        else:
            return super().default(v)


def json_error(e):
    # logger.exception(msg='JSON exception')
    return {'error': f'{type(e)}: {e}'}
