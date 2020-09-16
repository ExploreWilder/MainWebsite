from typing import List, Dict, Tuple, Union, Sequence, Any
from pymysql.cursors import Cursor as MySQLCursor
from flask import Response
FlaskResponse = Union[Response, Tuple[str, int]]
