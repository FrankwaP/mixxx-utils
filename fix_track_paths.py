"""Fix track paths in Mixxx library using your media player database.

So far only Clementine is supported but adapting the scripts to other media players should be easy.
"""

from python_tools.fix_track_paths_utils.clementine import (
    fix_with_clementine_db,
)

if __name__ == "__main__":
    fix_with_clementine_db()
