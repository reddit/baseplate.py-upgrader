# Baseplate.py Upgrader

This tool will help you make the changes necessary to upgrade your Baseplate.py
service from one version to another.

The easiest way to use this tool is through `pipx` (`brew install pipx` on
macOS):

    pipx run --spec git+https://github.com/reddit/baseplate.py-upgrader baseplate.py-upgrader ~/src/fooservice

You can also create a virtualenv and install it manually:

    python3.12 -m venv venv
    venv/bin/pip install git+https://github.com/reddit/baseplate.py-upgrader
    venv/bin/baseplate.py-upgrader ~/src/fooservice
