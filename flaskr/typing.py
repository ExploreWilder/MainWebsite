"""
Common type definitions.
"""

# pylint: disable=unused-import

from typing import Any
from typing import Dict
from typing import List
from typing import Sequence
from typing import Tuple
from typing import Union

from flask import Response
from pymysql.cursors import Cursor as MySQLCursor

FlaskResponse = Union[Response, Tuple[str, int]]
