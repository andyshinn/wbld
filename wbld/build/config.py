from configparser import ConfigParser


class CustomConfigException(Exception):
    def __init__(self, cc, message="Too many sections in configuration"):
        self.message = message

        if cc:
            self.message += f": {len(cc)}"

        super(CustomConfigException, self).__init__(self.message)


class CustomConfig(ConfigParser):
    def __init__(self, snippet):
        super(CustomConfig, self).__init__()
        self.snippet = snippet
        self.read_string(self.snippet)

        if len(self) > 1:
            raise CustomConfigException(self)

    def __len__(self):
        return len(self._sections)

    def __str__(self):
        return self.snippet

    @staticmethod
    def remove_prefix(text, prefix):
        if text.startswith(prefix):
            return text[len(prefix) :]
        return text

    @property
    def section(self):
        return self.sections()[0]

    @property
    def env(self):
        return CustomConfig.remove_prefix(self.section, "env:")

    @property
    def config(self):
        return self[self.section]

    @property
    def pc_config(self):
        return [(self.section, list(self.config.items()))]
