from inspect import getmembers
from sys import exit
from types import ModuleType


# 0 star = "0", 1 star = "51", 2 stars = "102", 3 stars = "153", 4 stars = "204", 5 stars = "255"
RATING_MAPING = {0: 0, 1: 51, 2: 102, 3: 153, 4: 204, 5: 255}

# made using the SQL command "SELECT DISTINCT key_id, key FROM library"
# then some Regex…
KEY_ID_LANCELOT = {
    21: "1A",
    12: "1B",
    16: "2A",
    7: "2B",
    23: "3A",
    2: "3B",
    18: "4A",
    9: "4B",
    13: "5A",
    4: "5B",
    20: "6A",
    11: "6B",
    15: "7A",
    6: "7B",
    22: "8A",
    1: "8B",
    17: "9A",
    8: "9B",
    24: "10A",
    3: "10B",
    19: "11A",
    10: "11B",
    14: "12A",
    5: "12B",
}


def confirm_config(config_module: ModuleType):
    members = getmembers(config_module)
    params = sorted(
        i for i in members if not i[0].startswith("__") and "." not in str(i[1])
    )
    if params:
        print(
            "The following parameters have been defined in the "
            f"{config_module.__name__}.py file:"
        )
        for param in params:
            print(f"{param[0]}:\t{param[1]}")
        answer = input("\nAre you OK with these settings (y/*)?\t: ")
        if answer != "y":
            exit(1)
