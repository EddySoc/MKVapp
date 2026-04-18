"""
Standalone worker: moves files to the recycle bin via PowerShell.
Called as subprocess by common.py.
Args: one or more file paths as command-line arguments.
Prints OK:<path> or ERROR:<path>:<message> per file.
"""
import sys
import subprocess
import os


def recycle_via_powershell(path: str) -> None:
    """Use PowerShell + Microsoft.VisualBasic to move to recycle bin."""
    path = os.path.abspath(path).replace("'", "''")
    ps_cmd = (
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        f"[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("
        f"'{path}', 'OnlyErrorDialogs', 'SendToRecycleBin')"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"exit {result.returncode}")


if __name__ == "__main__":
    paths = sys.argv[1:]
    if not paths:
        print("ERROR::No paths given")
        sys.exit(1)

    for path in paths:
        try:
            if not os.path.exists(path):
                print(f"NOTFOUND:{path}")
                continue
            recycle_via_powershell(path)
            print(f"OK:{path}", flush=True)
        except Exception as e:
            print(f"ERROR:{path}:{e}", flush=True)
