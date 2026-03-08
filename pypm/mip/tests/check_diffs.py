import os.path
import glob
import difflib
import subprocess
import sys

def run_diff(file1_path, file2_path):
    """
    Runs the system's 'diff' command and prints the output.
    """
    try:
        # The 'capture_output=True' argument captures stdout and stderr
        # 'text=True' ensures output is handled as strings
        result = subprocess.run(
            ['diff', file1_path, file2_path],
            capture_output=True,
            text=True,
            check=False # Set check=True if you want an exception on non-zero exit (files differ)
        )
        print(result.stdout)
    except FileNotFoundError:
        print("Error: 'diff' command not found. Are you on a Linux/macOS system?")
    except Exception as e:
        print(f"An error occurred: {e}")


for test in sorted(glob.glob(f'{sys.argv[1]}/test*[0-9].yaml')):
    name = os.path.basename(test)
    print(name)
    run_diff(test, os.path.join(sys.argv[2],name))
