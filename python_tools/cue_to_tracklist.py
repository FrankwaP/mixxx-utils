"""A tool to generate a tracklist for Soundcloud/Youtube/… from a Mixxx's cue file"""

from sys import argv
from pathlib import Path


class TrackObj:
    def __init__(self):
        self.artist = "ID"
        self.title = "ID"
        self.time = "XX:XX"

    def __str__(self):
        return f"{self.time}\t{self.artist} - {self.title}"


def get_tracks_dict_list(cue_file: Path) -> list[TrackObj]:
    track_obj_list = []
    with open(cue_file, "r") as fcue:
        for line in fcue:
            line = line.strip()
            if line.startswith("TRACK"):
                track_obj = TrackObj()
                track_obj_list.append(track_obj)
            elif line.startswith("TITLE"):
                track_obj.title = line[7:-1]
            elif line.startswith("PERFORMER"):
                track_obj.artist = line[11:-1]
            elif line.startswith("INDEX"):
                # index is in "mm:ss:ff (minute-second-frame)"
                track_obj.time = line[9:-3]
    return track_obj_list


def write_track_obj_list(txt_file: Path, track_obj_list: list[TrackObj]) -> None:
    with open(txt_file, "w") as ftxt:
        for track_obj in track_obj_list:
            ftxt.write(f"{track_obj}\n")


def genereate_tracklist_file(cue_file: Path) -> None:
    track_obj_list = get_tracks_dict_list(cue_file)
    txt_file = cue_file.with_suffix(".txt")
    write_track_obj_list(txt_file, track_obj_list)
    print(f"==> {txt_file}")


def remove_file_quotes(path: str) -> str:
    """
    Remove the quotes around the file name.

    When using drag and drop to easily get a file name in a terminal, quotes can be added
    to this file name.
    """
    if path[0] in ["'", '"'] and path[-1] in ["'", '"']:
        path = path[1:-1]
    return path


if __name__ == "__main__":
    if len(argv) == 1:
        print("Please use files names as arguments")
    else:
        for cue_file in argv[1:]:
            pcue = Path(remove_file_quotes(cue_file))
            if pcue.exists() and pcue.suffix == ".cue":
                genereate_tracklist_file(pcue)
            else:
                print("File does not exist or is not a cue file.")
