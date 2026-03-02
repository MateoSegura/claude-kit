"""Plugin decryption and temp directory management.

Uses only stdlib (pathlib, shutil, tempfile, time) — no third-party deps.

Security: The encryption key is always injected by the caller. This module
never assembles, stores, or has any knowledge of how the key is derived.
"""

from __future__ import annotations

import shutil
import tempfile
import time
from pathlib import Path


class PluginDecryptor:
    """Decrypt AES-256-CBC encrypted plugin content.

    Args:
        key: Encryption passphrase. The library never assembles this
            value — it is always injected by the caller.
    """

    def __init__(self, key: str) -> None:
        self.key = key

    def is_encrypted(self, plugin_dir: Path) -> bool:
        """Check if a plugin directory contains content.enc."""
        return plugin_dir.exists() and (plugin_dir / "content.enc").exists()

    def decrypt(self, plugin_dir: Path, dest_dir: Path) -> Path:
        """Decrypt plugin content into dest_dir.

        Extracts the tar.gz archive inside content.enc using openssl,
        merges with plaintext metadata files (plugin.json, ctl.json, README.md).

        Returns the path to the decrypted plugin directory.
        Raises DecryptionError on failure.
        """
        import io
        import subprocess
        import tarfile

        from claude_kit.exceptions import DecryptionError

        plugin_name = plugin_dir.name
        out_dir = dest_dir / plugin_name
        out_dir.mkdir(parents=True, exist_ok=True)

        # Copy metadata files (plaintext)
        cp_dir = plugin_dir / ".claude-plugin"
        if cp_dir.exists():
            shutil.copytree(cp_dir, out_dir / ".claude-plugin", dirs_exist_ok=True)

        enc_file = plugin_dir / "content.enc"
        if not enc_file.exists():
            return out_dir

        result = subprocess.run(
            [
                "openssl",
                "enc",
                "-d",
                "-aes-256-cbc",
                "-pbkdf2",
                "-iter",
                "100000",
                "-pass",
                f"pass:{self.key}",
                "-in",
                str(enc_file),
            ],
            capture_output=True,
        )
        if result.returncode != 0:
            raise DecryptionError(f"Failed to decrypt plugin '{plugin_name}'")

        with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:gz") as tar:
            tar.extractall(path=str(out_dir))

        return out_dir


class TempDirManager:
    """Track and clean up temporary directories for decrypted plugins."""

    def __init__(self) -> None:
        self.temp_dirs: list[Path] = []

    def create(self, prefix: str = "claude-kit-") -> Path:
        """Create a temp directory and register it for cleanup."""
        d = Path(tempfile.mkdtemp(prefix=prefix))
        self.temp_dirs.append(d)
        return d

    def cleanup(self) -> None:
        """Remove all registered temp directories."""
        for d in self.temp_dirs:
            try:
                shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass
        self.temp_dirs.clear()

    def cleanup_stale(self, base_dir: Path, max_age_hours: int = 24) -> int:
        """Remove temp dirs matching ck-* older than max_age_hours.

        Returns count of directories removed.
        """
        cutoff = time.time() - (max_age_hours * 3600)
        removed = 0
        for d in base_dir.glob("ck-*"):
            if d.is_dir():
                try:
                    if d.stat().st_mtime < cutoff:
                        shutil.rmtree(d, ignore_errors=True)
                        removed += 1
                except OSError:
                    pass
        return removed
