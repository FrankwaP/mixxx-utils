from sys import exit
from inspect import getmembers
from types import ModuleType


def confirm_config(config_module: ModuleType):
    members = getmembers(config_module)
    params = [i for i in members if not i[0].startswith("__")]
    print(
        "The following parameters have been defined in the "
        f"{config_module.__name__}.py file:"
    )
    for param in params:
        print(f"{param[0]}:\t{param[1]}")
    answer = input("\nAre you OK with these settings (y/*)?\t: ")
    if answer != "y":
        exit(1)
