import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import validity


class Command(BaseCommand):
    help = "Makes symlinks inside $SCRIPTS_ROOT dir for Validity scripts"

    plugin_scripts_dir = "scripts"
    script_prefix = "validity_"

    def handle(self, *args, **options):
        validity_scripts = Path(validity.__file__).parent.absolute() / self.plugin_scripts_dir
        self.symlink_scripts(Path(validity_scripts), Path(settings.SCRIPTS_ROOT))

    def symlink_scripts(self, src_dir: Path, dst_dir: Path) -> None:
        symlinks_created = 0
        for script_file in Path(src_dir).iterdir():
            if not script_file.is_file() or not script_file.name.endswith(".py") or script_file.name == "__init__.py":
                continue
            dst_file = dst_dir / (self.script_prefix + script_file.name)
            if dst_file.is_file() or dst_file.is_symlink():
                continue
            try:
                os.symlink(script_file, dst_file)
                self.stdout.write(self.style.SUCCESS(f"Symlink created: {dst_file} -> {script_file}"))
                symlinks_created += 1
            except OSError as e:
                raise CommandError(f"Cannot make the symlink {dst_file} -> {script_file}, {type(e).__name__}: {e}")
        self.stdout.write(f"Symlinks created: {symlinks_created}")
