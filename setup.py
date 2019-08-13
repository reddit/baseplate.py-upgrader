from setuptools import setup, find_packages

setup(
    name="baseplate_py_upgrader",
    packages=find_packages(),
    python_requires=">=3.7.0",
    entry_points={
        "console_scripts": ["baseplate.py-upgrader=baseplate_py_upgrader:main"]
    },
)
