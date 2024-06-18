# Suggestions for Git/Python noob

## Dowloading this repo

You probably do not have Git installed and do not want to mess with it… so you can directly [download a zip of the reposit](https://github.com/FrankwaP/mixxx-utils/archive/refs/heads/main.zip) and unzip it where you want.

Note that you'll have to do this each time a modification is made. That would be an advantage of installing (and using) Git: you'd first `git clone` then a siple `git pull` will automatically update the content of the reposit.

## Installing Python and the required library

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

Please see the README.md files in each specific folder.
