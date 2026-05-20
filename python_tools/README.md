# Python tools

## Configuration

The different tools get their configuration from a toml file that is specified through the
`MIXXX_UTILS_CONFIG` environment variable or will default to a file named `config.toml` in the
[python_tools](python_tools) directory.
See the provided [example.config.toml](example.config.toml) file for details.


## Installing Python and the required libraries

**NOTE**: I know it's a bit of a chicken and egg problem, but since I do not think that this project will get big, I consider the majority of the users finding this work on github
will be fine using a terminal… once again: [YAGNI](https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it)…


This is a method which does not need you to use administrator/sudo account.

First [install Mambaforge](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html) with the default settings.

Now open a terminal (omg so scary :-p ) and:

1. Change the path:
   1. On Windows type `chdir̀ /D` and on Linux type `cd`
   2. Then go back to the windows you've opened, and drag&drop the `python_tools` folder, which will write the path to the folder. So you end up with something like `chdir /D D:\...\python_tools` or `cd /home/.../python_tools`.
   3. Execute the command (press "Enter")
2. Create an Mamba environment:`mamba create --name mixxx-utils --file requirements-conda.txt`. (An "environment" is simply a folder with compatible executables and libraries.)
3. Activate this new environment: `mamba activate mixxx-utils`. ("Activating" means that the executables and libraries in the environement folder will be used when you execute code.)
4. Install the libraries that can only be installed with `pip` (package installer for Python): `pip install --requirement requirements-pip.txt`


## Running the scripts

**NOTE**: Remember to activate the Python environment if you are using one (pipenv/anaconda…) :-)

BASH scripts are available to use the Python scripts in Lunx.

Some of them are very simple, like [mixxx_to_rekordbox.sh](mixxx_to_rekordbox.sh), because they only read Mixxx library.
In this case it is pretty straightforward to use the same command in Windows or Mac.

However the ones modifying Mixxx library, such as [fix_track_paths.sh](fix_track_paths.sh) and [fix_track_paths.sh](fix_track_paths.sh), are more complex since they call `sqlite3` function to edit the database. This was the chosen solution at the beginning of this project since Mixxx could not open a database exported using `pandas`. But I rekon this has to be improved so we can do it all in Python.
