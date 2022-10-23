"""
create bitcoin schema
"""

from typing import Any

from yoyo import step

__depends__: Any = {}

steps = [step("CREATE SCHEMA bitcoin", "DROP SCHEMA bitcoin")]
