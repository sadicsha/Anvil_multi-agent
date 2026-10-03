import subprocess
import tempfile
import sys
import os


def run_code_safely(code: str, test_code: str, timeout: int = 5):
    """
    Run generated Python code together with its tests in an isolated subprocess.
    Uses the active Python executable (sys.executable) to ensure environment parity.
    """
    full_script = (code or "") + "\n\n" + (test_code or "")

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    ) as f:
        f.write(full_script)
        path = f.name

    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )

        output = (result.stdout or "") + (result.stderr or "")
        return result.returncode == 0, output

    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout} seconds."

    except Exception as e:
        return False, f"Execution error: {str(e)}"

    finally:
        if os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass