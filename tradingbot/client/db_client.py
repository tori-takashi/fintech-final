from configparser import SafeConfigParser
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.interfaces import PoolListener
from sqlalchemy.ext.declarative import declarative_base

from model.base import Base
from .config import Config

from influxdb import DataFrameClient


class DBClient:
    def __init__(self, db_type, config_path):
        self.config = Config(config_path).config
        self.db_type = db_type
        self.connector = self.establish_connection_to_db()

        if self.is_influxdb() is not True:
            Session = sessionmaker(self.connector)
            self.session = Session()

            Base.metadata.create_all(bind=self.connector)

    def is_mysql(self):
        return self.db_type == "mysql"

    def is_influxdb(self):
        return self.db_type == "influxdb"

    def establish_connection_to_db(self):
        if self.is_mysql():
            return self.mysql_establish_connection()
        elif self.is_influxdb():
            return self.influxdb_establish_connection()

    def mysql_establish_connection(self):
        conf = self.config['mysql']
        url = "mysql+pymysql://" + \
            conf['username'] + ":" + conf['password'] + \
            "@" + conf['host'] + "/" + conf['db_name']
        return create_engine(url)

    def influxdb_establish_connection(self):
        return DataFrameClient(
            host=self.config['influxdb']['host'],
            port=int(self.config['influxdb']['port']),
            username=self.config['influxdb']['username'],
            password=self.config['influxdb']['password'],
            database=self.config['influxdb']['db_name']
        )

    def write_to_table(self, table_name, dataframe, if_exists):
        if self.is_mysql():
            dataframe.to_sql(table_name, self.connector,
                             if_exists=if_exists, index=False)
        if self.is_influxdb():
            # put all tags and fields before passing dataframe
            return self.connector.write_points(dataframe, table_name)

    def overwrite_to_table(self, table_name, dataframe):
        # for influx db is not available
        self.write_to_table(table_name, dataframe, if_exists="replace")

    def append_to_table(self, table_name, dataframe):
        self.write_to_table(table_name, dataframe, if_exists="append")

    def is_table_exist(self, table_name):
        if self.is_mysql():
            query = "SHOW TABLES LIKE '" + table_name + "';"
            results = self.exec_sql(query, return_df=False)
            for result in results:
                if result == (table_name,):
                    return True
                else:
                    return False

        if self.is_influxdb():
            return table_name in self.connector.get_list_measurements()

    def get_row_by_id(self, table_name, id):
        # only for mysql
        if self.is_mysql():
            query = "SELECT * FROM " + table_name + \
                " WHERE id = " + str(id) + ";"
        return self.query_return(query)

    def get_row_by_backtest_summary_id(self, table_name, backtest_summary_id):
        # only for mysql
        if self.is_mysql:
            query = "SELECT * FROM " + table_name + \
                " WHERE backtest_summary_id = " + \
                    str(backtest_summary_id) + ";"
        return self.query_return(query)

    def query_return(self, query):
        return_df = pd.read_sql_query(
            query, self.connector, index_col="id")

        if return_df.empty is not True:
            return return_df
        else:
            return False

    def get_last_row(self, table_name):
        # inly for mysql
        id = "(SELECT MAX(id) FROM " + table_name + ")"
        return self.get_row_by_id(table_name, id)

    def get_last_row_with_tags(self, measurement_name, tags):
        # only for influxdb
        results = self.connector.query("SELECT * FROM " + measurement_name)
        last_row = list(results.get_points(
            measurement=measurement_name, tags=tags))[-1]
        return last_row

    def exec_sql(self, query, return_df=True):
        if self.is_influxdb() is not True:
            if return_df:
                return pd.read_sql(query, self.connector, index_col="id")
            else:
                result_rows = self.connector.execute(query)
                return result_rows

        if self.is_influxdb():
            if return_df:
                pass
            else:
                return self.connector.query(query)

    def model_to_dataframe(self, model_list):
        return pd.DataFrame([model.__dict__ for model in model_list]).drop("_sa_instance_state", axis=1)
