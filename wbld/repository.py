import os
from pathlib import Path
from tempfile import TemporaryDirectory

from git import Repo
from github import Github, GithubException


class ReferenceException(Exception):
    def __init__(self, message="Could not find reference"):
        self.message = message
        super(ReferenceException, self).__init__(self.message)


class Reference:
    def __init__(self, reference, repository="Aircoookie/WLED"):
        self.reference = reference
        self.github = Github(os.getenv("GITHUB_TOKEN"))
        self.repository = self.github.get_repo(repository)

        checks = [self.get_commit, self.get_branch, self.get_tag]
        self.commit = next(x() for x in checks if x is not None)

        if not self.commit:
            raise ReferenceException

    def __str__(self):
        return self.commit.sha

    def get_commit(self):
        try:
            commit = self.repository.get_commit(self.reference)
        except GithubException:
            return False
        else:
            return commit

    def get_branch(self):
        try:
            branch = self.repository.get_branch(self.reference)
        except GithubException:
            return None
        else:
            return branch.commit

    def get_tag(self):
        for tag in self.repository.get_tags():
            if tag.name == self.reference:
                return tag.commit

        return None


class Clone:
    def __init__(self, url: str = "https://github.com/Aircoookie/WLED.git", cleanup: bool = True):
        self.tempdir = TemporaryDirectory()
        self._path = Path(self.tempdir.name)
        self.url = url
        self.repo = Repo.init(str(self.path))
        self._cleanup = cleanup
        self._version = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    @property
    def sha1(self):
        try:
            return self.repo.commit()
        except ValueError:
            return None

    @property
    def version(self):
        if not self._version:
            raise Exception("No version set")

        return self._version

    @property
    def path(self):
        if self._path.exists():
            return self._path
        else:
            raise FileNotFoundError("Path does not exist. Did you clone the repository?")

    def clone_version(self, version: str = "main"):
        self._version = version
        origin = self.repo.create_remote("origin", self.url)
        origin.fetch()
        self.repo.git.checkout(version)

        return self.sha1

    def cleanup(self):
        if self._cleanup:
            self.tempdir.cleanup()
