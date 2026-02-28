"""
=============================================================================
TEST 2: File Operations Tool — Simulation
=============================================================================
Tests FileOperations: reading, writing (atomic), backups, listing,
and security enforcement on all I/O.

Run:  python -m pytest tests/test_file_ops.py -v
=============================================================================
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.sandbox import SandboxManager
from src.tools.file_ops import FileOperations, FileOperationResult


@pytest.fixture
def sandbox_env(tmp_path):
    """Set up a sandbox with sample files for file operation tests."""
    sandbox_dir = tmp_path / "file_ops_sandbox"
    sandbox_dir.mkdir()

    # Create sample files
    (sandbox_dir / "sample.py").write_text("def hello():\n    return 'world'\n")
    (sandbox_dir / "empty.py").write_text("")
    (sandbox_dir / "subdir").mkdir()
    (sandbox_dir / "subdir" / "deep.py").write_text("x = 42\n")

    sandbox = SandboxManager(str(sandbox_dir))
    file_ops = FileOperations(sandbox)
    return sandbox, file_ops, sandbox_dir


class TestReadFile:
    """Test safe file reading."""

    def test_read_existing_file(self, sandbox_env):
        _, file_ops, _ = sandbox_env
        result = file_ops.read_file("sample.py")
        assert result.success is True
        assert "def hello" in result.content
        assert result.metadata["line_count"] >= 2
        print(f"  ✅ Read sample.py ({result.metadata['size_bytes']} bytes, {result.metadata['line_count']} lines)")

    def test_read_nonexistent_file(self, sandbox_env):
        _, file_ops, _ = sandbox_env
        result = file_ops.read_file("does_not_exist.py")
        assert result.success is False
        assert "not found" in result.error.lower() or "File not found" in result.error
        print(f"  ✅ Correctly failed for missing file: {result.error}")

    def test_read_empty_file(self, sandbox_env):
        _, file_ops, _ = sandbox_env
        result = file_ops.read_file("empty.py")
        assert result.success is True
        assert result.content == ""
        print("  ✅ Read empty file successfully")

    def test_read_nested_file(self, sandbox_env):
        _, file_ops, _ = sandbox_env
        result = file_ops.read_file("subdir/deep.py")
        assert result.success is True
        assert "42" in result.content
        print("  ✅ Read nested file subdir/deep.py")


class TestWriteFile:
    """Test safe (atomic) file writing."""

    def test_write_new_file(self, sandbox_env):
        _, file_ops, sandbox_dir = sandbox_env
        result = file_ops.write_file("output.py", "print('created!')\n")
        assert result.success is True
        # Verify content on disk
        content = (sandbox_dir / "output.py").read_text()
        assert content == "print('created!')\n"
        print(f"  ✅ Wrote new file: {result.filepath}")

    def test_write_overwrites_existing(self, sandbox_env):
        _, file_ops, sandbox_dir = sandbox_env
        file_ops.write_file("sample.py", "# overwritten\n", create_backup=False)
        content = (sandbox_dir / "sample.py").read_text()
        assert content == "# overwritten\n"
        print("  ✅ Overwrote existing file")

    def test_write_creates_backup(self, sandbox_env):
        _, file_ops, sandbox_dir = sandbox_env
        result = file_ops.write_file("sample.py", "# new content\n", create_backup=True)
        assert result.success is True
        # Check a backup file was created
        bak_files = list(sandbox_dir.glob("sample.py.bak.*"))
        assert len(bak_files) >= 1
        print(f"  ✅ Backup created: {bak_files[0].name}")


class TestCreateBackup:
    """Test backup creation."""

    def test_backup_existing_file(self, sandbox_env):
        _, file_ops, sandbox_dir = sandbox_env
        result = file_ops.create_backup("sample.py")
        assert result.success is True
        assert "backup_path" in result.metadata
        backup_path = result.metadata["backup_path"]
        assert os.path.exists(backup_path)
        print(f"  ✅ Backup at: {backup_path}")

    def test_backup_nonexistent_fails(self, sandbox_env):
        _, file_ops, _ = sandbox_env
        result = file_ops.create_backup("ghost.py")
        assert result.success is False
        print(f"  ✅ Backup correctly failed for missing file: {result.error}")


class TestListPythonFiles:
    """Test listing Python files."""

    def test_list_all_py_files(self, sandbox_env):
        _, file_ops, _ = sandbox_env
        result = file_ops.list_python_files()
        assert result.success is True
        assert result.metadata["count"] >= 3  # sample.py, empty.py, deep.py
        print(f"  ✅ Found {result.metadata['count']} Python files: {[os.path.basename(f) for f in result.metadata['files']]}")


class TestFileInfo:
    """Test getting file metadata."""

    def test_get_info_existing(self, sandbox_env):
        _, file_ops, _ = sandbox_env
        result = file_ops.get_file_info("sample.py")
        assert result.success is True
        assert result.metadata["is_file"] is True
        assert result.metadata["extension"] == ".py"
        print(f"  ✅ File info: size={result.metadata['size_bytes']}B, ext={result.metadata['extension']}")

    def test_get_info_missing(self, sandbox_env):
        _, file_ops, _ = sandbox_env
        result = file_ops.get_file_info("nope.py")
        assert result.success is False
        print(f"  ✅ Correctly failed for missing file")
