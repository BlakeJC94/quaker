import re
from git import Repo

# What to bump?
# * Determine which files have changed since the last commit to main
#   * If any non-specific file has changed, bump setup.py version
#   * If a config has changed, bump that
#     * Only config change? only bump that then
# How to bump?
# * Determine the tag from the github PR (ihavenoideahowtodothissoillassumeitfornow)
#   * Idea: config-major, config-minor, config-patch
# Do the bump
# * Bump eahc version in each version with major/minor/patch

ALLOWED_MODES = ["major", "minor", "patch"]
SEMVER_REGEX = r"\d+\.\d+\.\d+"

VERSIONED_FILES = [
    "quaker/core/cache.py",
]


def bump(version: str, mode: str) -> str:
    """Bumps a semver version.

    Args:
        version: string representing a semver version. Must have MAJOR.MINOR.PATCH format
        mode: Whether to bump 'major', 'minor', or 'patch'.

    Usage:
        >>> bump("1.2.3", "patch")
        '1.2.4'
        >>> bump("1.2.3", "minor")
        '1.3.0'
        >>> bump("1.2.3", "major")
        '2.0.0'
    """
    assert mode in ALLOWED_MODES, f"Invalid `mode` given, must be one of {ALLOWED_MODES}."
    assert re.match(
        SEMVER_REGEX, version
    ), "Invalid `version` given, must be a semver 'major.MINOR.PATCH' string."

    major, minor, patch = version.split(".")

    if mode == "major":
        major, minor, patch = str(int(major) + 1), "0", "0"
    if mode == "minor":
        minor, patch = str(int(minor) + 1), "0"
    if mode == "patch":
        patch = str(int(patch) + 1)

    return ".".join([major, minor, patch])


def get_files_to_bump():
    repo = Repo()

    # Get the git diff between this branch and main
    commit_branch = repo.commit()
    commit_origin_main = repo.commit("HEAD~1")
    diff = commit_origin_main.diff(commit_branch, create_patch=True, unified=0)

    # Find changed files
    changed_files = set()
    for diff_item in diff:
        if not diff_item.a_path:
            continue
        changed_files.add(diff_item.a_path)

    # Determine if only configs have changed (so then don't select setup.py)
    files_to_bump = {f for f in VERSIONED_FILES if f in changed_files}
    if any(v not in VERSIONED_FILES for v in changed_files):
        files_to_bump.add("setup.py")

    return files_to_bump
