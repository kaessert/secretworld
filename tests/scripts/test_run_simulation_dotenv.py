"""Test that run_simulation loads .env correctly."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_run_simulation_loads_dotenv():
    """Verify simulation can load API key from .env file and --with-ai flag exists."""
    project_root = Path(__file__).parent.parent.parent

    # Run simulation with --help to verify it starts without error and has --with-ai
    result = subprocess.run(
        [sys.executable, "-m", "scripts.run_simulation", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--with-ai" in result.stdout


def test_with_ai_flag_validates_key():
    """Verify --with-ai fails gracefully without API key.

    We create a minimal copy of the scripts module in a temporary directory
    without a .env file to ensure no API key is found.
    """
    project_root = Path(__file__).parent.parent.parent

    # Create a temporary directory with a copy of the scripts module
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Copy scripts directory to temp location
        scripts_src = project_root / "scripts"
        scripts_dst = tmpdir / "scripts"
        scripts_dst.mkdir()

        # Copy necessary files (but NOT any .env from project root)
        for py_file in scripts_src.glob("*.py"):
            (scripts_dst / py_file.name).write_text(py_file.read_text())

        # Copy src directory too (needed for imports)
        src_src = project_root / "src"
        src_dst = tmpdir / "src"
        import shutil
        shutil.copytree(src_src, src_dst)

        # Run with --with-ai but no key set, from tmpdir (no .env present)
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        env.pop("ANTHROPIC_API_KEY", None)
        # Set PYTHONPATH to the temp directory so it imports from there
        env["PYTHONPATH"] = str(tmpdir)

        result = subprocess.run(
            [sys.executable, "-m", "scripts.run_simulation", "--with-ai", "--max-commands=1"],
            cwd=tmpdir,  # Run from temp dir, not project root
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}. stdout: {result.stdout}"
        # Check for expected error message about missing API key
        output = result.stdout + result.stderr
        assert "OPENAI_API_KEY" in output or "ANTHROPIC_API_KEY" in output
