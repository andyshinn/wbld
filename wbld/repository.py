from tempfile import TemporaryDirectory
import os

from github import Github, GithubException
from git import Repo


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
    def __init__(self, version, url="https://github.com/Aircoookie/WLED.git"):
        self.path = TemporaryDirectory()
        self.url = url
        self.version = version
        self.repo = Repo.init(self.path.name)

    def __enter__(self):
        return self.path

    def __exit__(self, exc_type, exc_value, traceback):
        self.path.cleanup()

    def clone_version(self):
        origin = self.repo.create_remote("origin", self.url)
        origin.fetch()
        # repo.create_head('master', origin.refs.master)
        self.repo.git.checkout(self.version)

        return self.repo.commit()
