"""Tests for claude_kit.encryption — PluginDecryptor & TempDirManager contracts.

TDD: These tests define the expected behavior of encryption/decryption
utilities before implementation. Uses tmp_path fixtures.
"""

from __future__ import annotations

import time
from pathlib import Path

# ── Import & Construction ────────────────────────────────────────────────


def test_decryptor_importable():
    from claude_kit.encryption import PluginDecryptor  # noqa: F401


def test_temp_dir_manager_importable():
    from claude_kit.encryption import TempDirManager  # noqa: F401


def test_decryptor_stores_key():
    from claude_kit.encryption import PluginDecryptor

    d = PluginDecryptor(key="test-secret")
    assert d.key == "test-secret"


def test_decryptor_exported_from_package():
    from claude_kit import PluginDecryptor  # noqa: F401


def test_temp_dir_manager_exported_from_package():
    from claude_kit import TempDirManager  # noqa: F401


# ── is_encrypted() ───────────────────────────────────────────────────────


def test_is_encrypted_false_no_enc_file(tmp_path: Path):
    from claude_kit.encryption import PluginDecryptor

    plugin_dir = tmp_path / "test-plugin"
    plugin_dir.mkdir()
    d = PluginDecryptor(key="k")
    assert not d.is_encrypted(plugin_dir)


def test_is_encrypted_true_with_enc_file(tmp_path: Path):
    from claude_kit.encryption import PluginDecryptor

    plugin_dir = tmp_path / "test-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "content.enc").touch()
    d = PluginDecryptor(key="k")
    assert d.is_encrypted(plugin_dir)


def test_is_encrypted_false_nonexistent_dir(tmp_path: Path):
    from claude_kit.encryption import PluginDecryptor

    d = PluginDecryptor(key="k")
    assert not d.is_encrypted(tmp_path / "nonexistent")


# ── TempDirManager ───────────────────────────────────────────────────────


def test_temp_dir_create(tmp_path: Path):
    from claude_kit.encryption import TempDirManager

    mgr = TempDirManager()
    d = mgr.create(prefix="ck-test-")
    assert d.exists()
    assert d.is_dir()
    # Cleanup
    mgr.cleanup()


def test_temp_dir_tracked():
    from claude_kit.encryption import TempDirManager

    mgr = TempDirManager()
    d = mgr.create(prefix="ck-test-")
    assert d in mgr.temp_dirs
    mgr.cleanup()


def test_temp_dir_cleanup():
    from claude_kit.encryption import TempDirManager

    mgr = TempDirManager()
    d = mgr.create(prefix="ck-test-")
    assert d.exists()
    mgr.cleanup()
    assert not d.exists()


def test_temp_dir_cleanup_multiple():
    from claude_kit.encryption import TempDirManager

    mgr = TempDirManager()
    d1 = mgr.create(prefix="ck-test-")
    d2 = mgr.create(prefix="ck-test-")
    assert d1.exists()
    assert d2.exists()
    mgr.cleanup()
    assert not d1.exists()
    assert not d2.exists()


def test_temp_dir_cleanup_clears_list():
    from claude_kit.encryption import TempDirManager

    mgr = TempDirManager()
    mgr.create(prefix="ck-test-")
    mgr.cleanup()
    assert mgr.temp_dirs == []


def test_temp_dir_cleanup_ignores_already_removed():
    from claude_kit.encryption import TempDirManager

    mgr = TempDirManager()
    d = mgr.create(prefix="ck-test-")
    d.rmdir()  # manually remove before cleanup
    mgr.cleanup()  # should not raise
    assert mgr.temp_dirs == []


def test_temp_dir_cleanup_stale(tmp_path: Path):
    from claude_kit.encryption import TempDirManager

    # Create a "stale" directory
    stale = tmp_path / "ck-stale-123"
    stale.mkdir()
    # Backdate mtime by 2 hours
    old_time = time.time() - 7200
    import os

    os.utime(stale, (old_time, old_time))

    # Create a "fresh" directory
    fresh = tmp_path / "ck-fresh-456"
    fresh.mkdir()

    mgr = TempDirManager()
    removed = mgr.cleanup_stale(tmp_path, max_age_hours=1)
    assert removed == 1
    assert not stale.exists()
    assert fresh.exists()


def test_temp_dir_cleanup_stale_no_matches(tmp_path: Path):
    from claude_kit.encryption import TempDirManager

    # No ck-* directories
    mgr = TempDirManager()
    removed = mgr.cleanup_stale(tmp_path, max_age_hours=1)
    assert removed == 0


# ── Security boundary ────────────────────────────────────────────────────


def test_encryption_module_has_no_get_key():
    """The library must never contain key assembly logic."""
    import inspect

    import claude_kit.encryption as mod

    source = inspect.getsource(mod)
    assert "_get_key" not in source
    assert "key_part" not in source.lower()
