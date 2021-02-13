import sys

import pkg_resources

from pipepy import git

if __name__ == "__main__":
    # Lets eat our own dogfood :)
    git_tag = str(git.describe(tags=True)).strip()
    print(f"git tag    is: {git_tag}")

    python_tag = pkg_resources.require('pipepy')[0].version
    print(f"python tag is: {python_tag}")

    if git_tag == python_tag:
        print("Versions match, proceeding")
        sys.exit(0)
    else:
        print("Versions don't match, stopping")
        sys.exit(1)
