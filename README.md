# Baseplate.py Upgrader

This tool will help you make the changes necessary to upgrade your Baseplate.py
service from one version to another.

Install the upgrader on your development machine (outside any VMs, since this
will be editing source code):

    pip3.7 install git+https://github.com/reddit/baseplate.py-upgrader

and then run it on a baseplate.py project you want to upgrade:

    baseplate.py-upgrader ~/src/fooservice
