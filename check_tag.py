import sys
import pkg_resources

from pipepy import git

if __name__ == "__main__":
    git_tag = str(git.describe(tags=True)).strip()
    python_tag = pkg_resources.require('pipepy')[0].version
    if git_tag == python_tag:
        sys.exit(0)
    else:
        sys.exit(1)
