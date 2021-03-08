import logging
import re

from pathlib import Path
from typing import Match


logger = logging.getLogger(__name__)


IMAGE_RE = re.compile(
    r"/baseplate-py:(?P<version>[0-9.]+(\.[0-9]+)?)-py(?P<python>[23]\.[0-9]+)-(?P<distro>(bionic|buster))(?P<repo>-artifactory)?(?P<dev>-dev)?"
)


def upgrade_docker_image_references_in_file(target_series: str, filepath: Path) -> None:
    major, minor = target_series.split(".")
    if major == "0":
        image_series = f"{major}.{minor}"
    else:
        image_series = f"{major}"

    force_distro = None
    force_dev = False
    force_repo = None
    if major == "2":
        force_distro = "buster"
        force_dev = True
        force_repo = ""

    def replace_docker_image_reference(m: Match[str]) -> str:
        distro = force_distro or m["distro"]
        repo = force_repo if force_repo is not None else m["repo"]
        dev = "-dev" if force_dev else m["dev"]
        return f"/baseplate-py:{image_series}-py{m['python']}-{distro}{repo or ''}{dev or ''}"

    file_content = filepath.read_text()
    changed = IMAGE_RE.sub(replace_docker_image_reference, file_content, re.MULTILINE)

    if file_content == changed:
        return

    with filepath.open("w") as f:
        logger.info("Updated Docker image references in %s", filepath)
        f.write(changed)


def upgrade_docker_image_references(target_series: str, root: Path) -> None:
    for dockerfile in root.glob("**/Dockerfile*"):
        upgrade_docker_image_references_in_file(target_series, dockerfile)

    dronefile = root / ".drone.yml"
    if dronefile.exists():
        upgrade_docker_image_references_in_file(target_series, dronefile)
