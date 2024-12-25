from pathlib import Path


def merge_directories(src: Path, dst: Path) -> None:
    """
    Move all files from src to dst with rewriting
    """
    for item in src.rglob("*"):
        target = dst / item.relative_to(src)

        if item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            item.rename(target)
        elif item.is_dir():
            target.mkdir(parents=True, exist_ok=True)

    if not any(src.iterdir()):
        src.rmdir()
