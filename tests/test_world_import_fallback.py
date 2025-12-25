"""Tests for world module AI import fallback behavior (lines 18-21).

This test uses subprocess with coverage to test the import fallback behavior
while still tracking coverage. The subprocess approach is necessary because
the import error handling happens at module load time.
"""

import os
import subprocess
import sys
import tempfile


class TestAIImportFallback:
    """Tests for AI import fallback behavior (lines 18-21)."""

    def test_ai_import_failure_sets_fallback_values(self):
        """Test that ImportError sets AI_AVAILABLE=False and mocks to None.

        Spec: When ai_service/ai_world imports fail, AI_AVAILABLE should be False
        and AIService/create_ai_world should be None (lines 18-21).

        Uses subprocess with coverage tracking to measure the except block.
        """
        # Python code to run in subprocess
        test_code = '''
import sys
import builtins

# Intercept the import machinery to raise ImportError for AI modules
original_import = builtins.__import__

def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name in ('cli_rpg.ai_service', 'cli_rpg.ai_world'):
        raise ImportError(f"Mocked ImportError for {name}")
    return original_import(name, globals, locals, fromlist, level)

builtins.__import__ = mock_import
try:
    # Now import world - this should hit the except block
    import cli_rpg.world as test_world

    # Verify the except block set the fallback values
    assert test_world.AI_AVAILABLE is False, f"Expected AI_AVAILABLE=False, got {test_world.AI_AVAILABLE}"
    assert test_world.AIService is None, f"Expected AIService=None, got {test_world.AIService}"
    assert test_world.create_ai_world is None, f"Expected create_ai_world=None, got {test_world.create_ai_world}"

    print("SUCCESS: Import fallback test passed")
finally:
    builtins.__import__ = original_import
'''

        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Write test code to a temp file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, dir=project_root
        ) as f:
            f.write(test_code)
            temp_file = f.name

        try:
            # Run subprocess with coverage enabled
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.join(project_root, 'src')
            # Tell coverage to write to a unique data file
            env['COVERAGE_FILE'] = os.path.join(project_root, '.coverage.import_fallback')

            result = subprocess.run(
                [
                    sys.executable, '-m', 'coverage', 'run',
                    '--source=cli_rpg.world',
                    '--parallel-mode',
                    temp_file
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=project_root,
                env=env
            )

            # Check that the subprocess succeeded
            assert result.returncode == 0, (
                f"Subprocess failed with code {result.returncode}:\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
            assert "SUCCESS" in result.stdout, (
                f"Test did not succeed:\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
