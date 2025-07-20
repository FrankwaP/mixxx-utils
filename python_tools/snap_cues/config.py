from typing import Final

from python_tools import get_config

_config = get_config()["snap_cues"]

# parameters for snap_cues.py
# (Fixing tracks locations)
# The names MUST correspond to the ones in mixxxdb_fix_cues.sql file
# You normally do not need to change them
CUSTOM_DB: Final[str] = _config["custom_db"]
CUSTOM_DB_TABLE_NAME: Final[str] = _config["custom_db_table_name"]
# Cues index to modify
IDX_SNAPPED_CUES: Final[list[int]] = _config["idx_snapped_cues"]
