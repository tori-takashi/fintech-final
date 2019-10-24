from configparser import SafeConfigParser
import sqlite3
import pandas as pd


class DBClient:
    def __init__(self, db_type, opt=None):
        self.config = SafeConfigParser()
        self.opt = opt

        # config.ini should be same place to executing file
        self.config.read("config.ini")
        self.client = self.establish_connection_to_db(db_type)
        self.cursor = self.client.cursor()

    def establish_connection_to_db(self, db_type):
        if db_type == "sqlite3":
            return self.sqlite3_establish_connection()

    def sqlite3_establish_connection(self):
        if self.opt == None:
            return sqlite3.connect(self.config['sqlite3']['db_path'])
        else:
            return sqlite3.connect(self.opt)
