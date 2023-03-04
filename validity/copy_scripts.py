import hashlib
import logging
import shutil
from pathlib import Path


logger = logging.getLogger(__name__)


def hashes_equal(src: Path, dst: Path) -> bool:
    with open(src, "r") as src_file, open(dst, "r") as dst_file:
        src_digest = hashlib.md5(src_file.read().encode()).hexdigest()
        dst_digest = hashlib.md5(dst_file.read().encode()).hexdigest()
        return src_digest == dst_digest


def copy_scripts(src_dir: Path, dst_dir: Path):
    for script_file in Path(src_dir).iterdir():
        if not script_file.is_file() or not script_file.name.endswith(".py") or script_file.name == "__init__.py":
            continue
        dst_file_path = dst_dir / f"validity_{script_file.name}"
        if not dst_file_path.is_file() or not hashes_equal(script_file, dst_file_path):
            logger.warning("Copying script %s to %s", script_file.name, dst_file_path)
            shutil.copy(script_file, dst_file_path)
