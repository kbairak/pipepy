import sys
import tomllib


def get_version():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


if __name__ == "__main__":
    import subprocess

    git_tag = (
        subprocess.run(
            ["git", "describe", "--tags"],
            capture_output=True, text=True
        )
        .stdout.strip()
    )
    print(f"git tag    is: {git_tag}")

    python_tag = get_version()
    print(f"python tag is: {python_tag}")

    if git_tag == python_tag:
        print("Versions match, proceeding")
        sys.exit(0)
    else:
        print("Versions don't match, stopping")
        sys.exit(1)
