from pathlib import Path
from shutil import copyfile
from typing import Optional

from tqdm import tqdm
from tqdm.contrib.concurrent import process_map


def _copyfile(orig_dest: tuple[str, str]):
    orig, dest = orig_dest
    Path(Path(dest).parent).mkdir(parents=True, exist_ok=True)
    copyfile(orig, dest)
