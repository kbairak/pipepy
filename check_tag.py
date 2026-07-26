import sys
from importlib.metadata import version as get_version

from pipepy import git

if __name__ == "__main__":
    git_tag = str(git.describe(tags=True)).strip()
    print(f"git tag    is: {git_tag}")

    python_tag = get_version("pipepy")
    print(f"python tag is: {python_tag}")

    if git_tag == python_tag:
        print("Versions match, proceeding")
        sys.exit(0)
    else:
        print("Versions don't match, stopping")
        sys.exit(1)
