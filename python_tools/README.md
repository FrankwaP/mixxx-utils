# Python tools

## Configuration

The different tools get their configuration from a toml file that is specified through the
`MIXXX_UTILS_CONFIG` environment variable or will default to a file named `config.toml` in the
[python_tools](python_tools) directory.
See the provided [example.config.toml](example.config.toml) file for details.

## Installing Python and the required libraries

I haven't prepared an executable yet, so you need to:

- install Python 3.11
- (maybe) create an environment
- install the requirements with `pip install python_tools/requirements-pip.txt`

It is explained in details in this [Ultimate Python Venv Tutorial and Guide](https://gist.github.com/basperheim/17e169478aa1be3cacbd9c530afeb155#file-python-venv-tutorial-md).

## Running the scripts

You simply need to execute the various Python files in the root directory of this project: `python name_of_the_util.py`.

**NOTE**: Remember to activate the Python environment if you are using one :-)
