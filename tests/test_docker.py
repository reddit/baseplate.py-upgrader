import pytest

from baseplate_py_upgrader.docker import replace_docker_image_references


@pytest.mark.parametrize(
    ("input", "expected"),
    (
        (
            "FROM example.com/baseplate-py:0.30-py3.6-bionic-dev",
            "FROM example.com/baseplate-py:2-py3.6-buster-dev",
        ),
        (
            "FROM example.com/baseplate-py:1-py3.8-bionic",
            "FROM example.com/baseplate-py:2-py3.8-buster-dev",
        ),
        (
            "FROM example.com/baseplate-py:1-py3.8-bionic-dev",
            "FROM example.com/baseplate-py:2-py3.8-buster-dev",
        ),
        (
            "FROM example.com/baseplate-py:2-py3.9-buster",
            "FROM example.com/baseplate-py:2-py3.9-buster",
        ),
    ),
)
def test_replace_docker_image_references(input, expected):
    output = replace_docker_image_references("2.0", input)
    assert output == expected
