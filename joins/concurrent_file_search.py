import os
import platform
from os.path import isdir, join
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

mutex = Lock()
matches = []


def file_search(root, filename, executor):
    # print("Searching in:", root)
    try:
        entries = os.listdir(root)
    except PermissionError:
        # print(f"Permission denied, skipping: {root}") # Uncomment to see skipped directories
        return
    except OSError as e:
        # print(f"OS error accessing {root}: {e}, skipping.") # Uncomment to see other OS errors
        return

    for entry_name in entries:
        full_path = join(root, entry_name)

        if (
            filename in entry_name
        ):  # Check if filename is part of the current entry's name
            with mutex:  # Use context manager for lock
                matches.append(full_path)

        if isdir(full_path):
            executor.submit(file_search, full_path, filename, executor)


def main():
    system = platform.system()
    if system == "Windows":
        search_path = "c:/tools"
    elif system == "Darwin":  # macOS
        search_path = "/Users"
    else:
        print(f"Unsupported OS: {system}. Defaulting to current directory.")
        search_path = "."

    # Determine a reasonable number of workers
    # os.cpu_count() can return None, so provide a fallback.
    num_workers = os.cpu_count() or 4

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit the initial search task.
        # The `with` statement will ensure that we wait for this task
        # and all tasks it recursively submits to complete before proceeding.
        executor.submit(file_search, search_path, "README.md", executor)

    for m in matches:
        print("Matched:", m[:3])  # Preserving user's change m[:3]


main()
