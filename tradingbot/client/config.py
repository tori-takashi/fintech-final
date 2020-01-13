from configparser import SafeConfigParser


class Config:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = SafeConfigParser()
        self.config.read(self.config_path)
