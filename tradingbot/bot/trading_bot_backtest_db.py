from datetime import timedelta

import numpy as np
import pandas as pd

from sqlalchemy import Column, Integer, Float, Table, MetaData
from sqlalchemy import update
from sqlalchemy.orm import relationship, mapper

from alembic.migration import MigrationContext
from alembic.operations import Operations

from lib.dataset import Dataset

from model.backtest_management import BacktestManagement
from model.backtest_summary import BacktestSummary

class TradingBotBacktestDB:
    def __init__(self, tradingbot, is_backtest):
        self.tradingbot = tradingbot
        self.db_client = tradingbot.db_client
        self.exchange_client = tradingbot.exchange_client
        self.backtest_management_table_name = self.tradingbot.bot_name + "_backtest_management"
        
        if self.has_backtest_table():
            # get_table_def_keys is method
            self.table_def_keys = tradingbot.append_specific_params_columns()
            self.create_backtest_management_table()

    def create_backtest_management_table(self):
        # add specific params columns
        backtest_management_template = BacktestManagement
        table_def = backtest_management_template.__table__

        table_def.name = self.backtest_management_table_name
        table_def      = self.append_backtest_specific_params_columns_to_table_def(table_def)
        table_def      = self.append_backtest_summary_id(table_def)

        table_def.create(bind=self.db_client.connector)
        
       # add foreign key constraint
        self.alter_add_foreign_key_to_backtest_summary()
        self.drop_backtest_management_template_table()
    
    def has_backtest_table(self):
        return self.db_client.is_table_exist(self.backtest_management_table_name) is not True

    def backtest_management_table(self):
        return Table(self.tradingbot.backtest_management_table_name, MetaData(bind=self.db_client.connector),
            autoload=True, autoload_with=self.db_client.connector)

    def append_backtest_specific_params_columns_to_table_def(self, table_def):
        for column_name, column_type in self.table_def_keys.items():
            table_def.append_column(Column(column_name, column_type))
        return table_def

    def append_backtest_summary_id(self, table_def):
        backtest_summary_id = Column("backtest_summary_id", Integer)
        table_def.relation = relationship("BacktestSummary")
        table_def.append_column(backtest_summary_id)
        return table_def

    def alter_add_foreign_key_to_backtest_summary(self):
        ctx = MigrationContext.configure(self.db_client.connector)
        op = Operations(ctx)

        with op.batch_alter_table(self.backtest_management_table_name) as batch_op:
            batch_op.create_foreign_key("fk_management_summary", "backtest_summary", ["backtest_summary_id"], ["id"])

    def drop_backtest_management_template_table(self):
        drop_query = "DROP TABLE backtest_management;"
        self.db_client.exec_sql(drop_query, return_df=False)

    def update_summary(self, transaction_logs, summary_id):
        self.transaction_logs_df = pd.DataFrame(transaction_logs)
        self.transaction_logs_df["holding_time"] = self.transaction_logs_df["close_time"] - \
            self.transaction_logs_df["entry_time"]

        win_row   = self.get_row_with_condition("win" , None)
        lose_row  = self.get_row_with_condition("lose", None)

        long_row  = self.get_row_with_condition(None, "long")
        short_row = self.get_row_with_condition(None, "short")

        win_long_row   = self.get_row_with_condition("win" , "long")
        win_short_row  = self.get_row_with_condition("win" , "short")
        lose_long_row  = self.get_row_with_condition("lose", "long")
        lose_short_row = self.get_row_with_condition("lose", "short")

        total_return = float(self.transaction_logs_df.profit_size.sum())
        total_return_percentage = self.calc_total_return_percentage(self.transaction_logs_df)

        long_average_holding_ms  = self.calc_holding_ms(long_row)
        short_average_holding_ms = self.calc_holding_ms(short_row)
        win_average_holding_ms   = self.calc_holding_ms(win_row)
        lose_average_holding_ms  = self.calc_holding_ms(lose_row)

        win_long_average_holding_ms   = self.calc_holding_ms(win_long_row)
        win_short_average_holding_ms  = self.calc_holding_ms(win_short_row)
        lose_long_average_holding_ms  = self.calc_holding_ms(lose_long_row)
        lose_short_average_holding_ms = self.calc_holding_ms(lose_short_row)

        win_consecutive = self.build_consecutive("win")
        lose_consecutive = self.build_consecutive("lose")
        drawdowns = self.build_drawdowns()
        recovery_factor = self.calc_recovery_factor(drawdowns["maximal_drawdown"], total_return)

        summary_dict = {
        "id": summary_id,
        "total_entry": len(self.transaction_logs_df),

        "total_max_holding_ms": self.transaction_logs_df["holding_time"].max().to_pytimedelta(),
        "total_average_holding_ms": self.transaction_logs_df["holding_time"].mean().to_pytimedelta(),
        "total_min_holding_ms": self.transaction_logs_df["holding_time"].min().to_pytimedelta(),

        "total_return": total_return,
        "total_return_average": float(self.transaction_logs_df.profit_size.mean()),
        "total_standard_deviation": float(self.transaction_logs_df.profit_size.std()),
        "total_skewness": float(self.transaction_logs_df.profit_size.skew()),
        "total_kurtosis": float(self.transaction_logs_df.profit_size.kurt()),
        "total_median": float(self.transaction_logs_df.profit_size.median()),

        "total_return_percentage": total_return_percentage,
        "total_return_average_percentage": float(self.transaction_logs_df.profit_percentage.mean()),
        "total_standard_deviation_percentage": float(self.transaction_logs_df.profit_percentage.std()),
        "total_skewness_percentage": float(self.transaction_logs_df.profit_percentage.skew()),
        "total_kurtosis_percentage": float(self.transaction_logs_df.profit_percentage.kurt()),
        "total_median_percentage": float(self.transaction_logs_df.profit_percentage.median()),

        "total_transaction_cost": float(self.transaction_logs_df.transaction_cost.sum()),

        # win
        "win_entry": len(win_row),
        "win_average_holding_ms": win_average_holding_ms,
        "win_rate": (len(win_row) / len(self.transaction_logs_df)) * 100,

        "win_return": float(win_row.profit_size.sum()),
        "win_return_average": float(win_row.profit_size.mean()),
        "win_standard_deviation": float(win_row.profit_size.std()),
        "win_skewness": float(win_row.profit_size.skew()),
        "win_kurtosis": float(win_row.profit_size.kurt()),
        "win_median": float(win_row.profit_size.median()),

        "win_return_average_percentage": float(win_row.profit_percentage.mean()),
        "win_standard_deviation_percentage": float(win_row.profit_percentage.std()),
        "win_skewness_percentage": float(win_row.profit_percentage.skew()),
        "win_kurtosis_percentage": float(win_row.profit_percentage.kurt()),
        "win_median_percentage": float(win_row.profit_percentage.median()),

        "win_transaction_cost": float(win_row.transaction_cost.sum()),
          
        "win_consecutive_max_entry": win_consecutive["consecutive_max_entry"],
        "win_consecutive_average_entry": win_consecutive["consecutive_average_entry"],
        "win_consecutive_max_profit": float(win_consecutive["consecutive_df"].profit_size.sum()),

        "win_max_profit": float(win_row.profit_size.max()),
        "win_max_profit_percentage": float(win_row.profit_percentage.max()),
                
        # lose
        "lose_entry": len(lose_row),
        "lose_rate": (len(lose_row) / len(self.transaction_logs_df)) * 100,
        "lose_average_holding_ms": lose_average_holding_ms,
    
        "lose_return": float(lose_row.profit_size.sum()),
        "lose_return_average": float(lose_row.profit_size.mean()),
        "lose_standard_deviation": float(lose_row.profit_size.std()),
        "lose_skewness": float(lose_row.profit_size.skew()),
        "lose_kurtosis": float(lose_row.profit_size.kurt()),
        "lose_median": float(lose_row.profit_size.median()),

        "lose_return_average_percentage": float(lose_row.profit_percentage.mean()),
        "lose_standard_deviation_percentage": float(lose_row.profit_percentage.std()),
        "lose_skewness_percentage": float(lose_row.profit_percentage.skew()),
        "lose_kurtosis_percentage": float(lose_row.profit_percentage.kurt()),
        "lose_median_percentage": float(lose_row.profit_percentage.median()),

        "lose_transaction_cost": float(lose_row.transaction_cost.sum()),

        "lose_consecutive_max_entry": lose_consecutive["consecutive_max_entry"],
        "lose_consecutive_average_entry": lose_consecutive["consecutive_average_entry"],
        "lose_consecutive_max_loss": float(lose_consecutive["consecutive_df"].profit_size.sum()),

        "lose_max_loss": float(lose_row.profit_size.min()),
        "lose_max_loss_percentage": float(lose_row.profit_percentage.min()),

        # long
        "long_entry": len(long_row),
        "long_rate": (len(long_row) / len(self.transaction_logs_df)) * 100,
        "long_average_holding_ms": long_average_holding_ms,

        "long_return": float(long_row.profit_size.sum()),
        "long_return_average": float(long_row.profit_size.mean()),
        "long_standard_deviation": float(long_row.profit_size.std()),
        "long_skewness": float(long_row.profit_size.skew()),
        "long_kurtosis": float(long_row.profit_size.kurt()),
        "long_median": float(long_row.profit_size.median()),

        "long_return_average_percentage": float(long_row.profit_percentage.mean()),
        "long_standard_deviation_percentage": float(long_row.profit_percentage.std()),
        "long_skewness_percentage": float(long_row.profit_percentage.skew()),
        "long_kurtosis_percentage": float(long_row.profit_percentage.kurt()),
        "long_median_percentage": float(long_row.profit_percentage.median()),
            
        "long_max_profit": float(long_row.profit_size.max()),
        "long_max_profit_percentage": float(long_row.profit_percentage.max()),

        "long_max_loss": float(long_row.profit_size.min()),
        "long_max_loss_percentage": float(long_row.profit_percentage.min()),

        #short
        "short_entry": len(short_row),
        "short_rate": (len(short_row) / len(self.transaction_logs_df)) * 100,
        "short_average_holding_ms": short_average_holding_ms,

        "short_return": float(short_row.profit_size.sum()),
        "short_return_average": float(short_row.profit_size.mean()),
        "short_standard_deviation": float(short_row.profit_size.std()),
        "short_skewness": float(short_row.profit_size.skew()),
        "short_kurtosis": float(short_row.profit_size.kurt()),
        "short_median": float(short_row.profit_size.median()),

        "short_return_average_percentage": float(short_row.profit_percentage.mean()),
        "short_standard_deviation_percentage": float(short_row.profit_percentage.std()),
        "short_skewness_percentage": float(short_row.profit_percentage.skew()),
        "short_kurtosis_percentage": float(short_row.profit_percentage.kurt()),
        "short_median_percentage": float(short_row.profit_percentage.median()),
            
        "short_max_profit": float(short_row.profit_size.max()),
        "short_max_profit_percentage": float(short_row.profit_percentage.max()),

        "short_max_loss": float(short_row.profit_size.min()),
        "short_max_loss_percentage": float(short_row.profit_percentage.min()),

        # win long
        "win_long_entry": len(win_long_row),
        "win_long_average_holding_ms": win_long_average_holding_ms,

        "win_long_return": float(win_long_row.profit_size.sum()),
        "win_long_return_average": float(win_long_row.profit_size.mean()),
        "win_long_standard_deviation": float(win_long_row.profit_size.std()),
        "win_long_skewness": float(win_long_row.profit_size.skew()),
        "win_long_kurtosis": float(win_long_row.profit_size.kurt()),
        "win_long_median": float(win_long_row.profit_size.median()),

        "win_long_return_average_percentage": float(win_long_row.profit_percentage.mean()),
        "win_long_standard_deviation_percentage": float(win_long_row.profit_percentage.std()),
        "win_long_skewness_percentage": float(win_long_row.profit_percentage.skew()),
        "win_long_kurtosis_percentage": float(win_long_row.profit_percentage.kurt()),
        "win_long_median_percentage": float(win_long_row.profit_percentage.median()),

        # win short
        "win_short_entry": len(win_short_row),
        "win_short_average_holding_ms": win_short_average_holding_ms,

        "win_short_return": float(win_short_row.profit_size.sum()),
        "win_short_return_average": float(win_short_row.profit_size.mean()),
        "win_short_standard_deviation": float(win_short_row.profit_size.std()),
        "win_short_skewness": float(win_short_row.profit_size.skew()),
        "win_short_kurtosis": float(win_short_row.profit_size.kurt()),
        "win_short_median": float(win_short_row.profit_size.median()),

        "win_short_return_average_percentage": float(win_short_row.profit_percentage.mean()),
        "win_short_standard_deviation_percentage": float(win_short_row.profit_percentage.std()),
        "win_short_skewness_percentage": float(win_short_row.profit_percentage.skew()),
        "win_short_kurtosis_percentage": float(win_short_row.profit_percentage.kurt()),
        "win_short_median_percentage": float(win_short_row.profit_percentage.median()),

        # lose long
        "lose_long_entry": len(lose_long_row),
        "lose_long_average_holding_ms": lose_long_average_holding_ms,

        "lose_long_return": float(lose_long_row.profit_size.sum()),
        "lose_long_return_average": float(lose_long_row.profit_size.mean()),
        "lose_long_standard_deviation": float(lose_long_row.profit_size.std()),
        "lose_long_skewness": float(lose_long_row.profit_size.skew()),
        "lose_long_kurtosis": float(lose_long_row.profit_size.kurt()),
        "lose_long_median": float(lose_long_row.profit_size.median()),

        "lose_long_return_average_percentage": float(lose_long_row.profit_percentage.mean()),
        "lose_long_standard_deviation_percentage": float(lose_long_row.profit_percentage.std()),
        "lose_long_skewness_percentage": float(lose_long_row.profit_percentage.skew()),
        "lose_long_kurtosis_percentage": float(lose_long_row.profit_percentage.kurt()),
        "lose_long_median_percentage": float(lose_long_row.profit_percentage.median()),

        # lose short
        "lose_short_entry": len(lose_short_row),
        "lose_short_average_holding_ms": lose_short_average_holding_ms,

        "lose_short_return": float(lose_short_row.profit_size.sum()),
        "lose_short_return_average": float(lose_short_row.profit_size.mean()),
        "lose_short_standard_deviation": float(lose_short_row.profit_size.std()),
        "lose_short_skewness": float(lose_short_row.profit_size.skew()),
        "lose_short_kurtosis": float(lose_short_row.profit_size.kurt()),
        "lose_short_median": float(lose_short_row.profit_size.median()),

        "lose_short_return_average_percentage": float(lose_short_row.profit_percentage.mean()),
        "lose_short_standard_deviation_percentage": float(lose_short_row.profit_percentage.std()),
        "lose_short_skewness_percentage": float(lose_short_row.profit_percentage.skew()),
        "lose_short_kurtosis_percentage": float(lose_short_row.profit_percentage.kurt()),
        "lose_short_median_percentage": float(lose_short_row.profit_percentage.median()),

        # other metrics
        "backtest_start_time": self.tradingbot.ohlcv_start_time,
        "backtest_end_time": self.tradingbot.ohlcv_end_time,

        "bot_name": self.tradingbot.default_params["bot_name"],
        "initial_balance": self.tradingbot.initial_balance,
        "account_currency": self.tradingbot.account_currency,

        "absolute_drawdown": float(drawdowns["absolute_drawdown"]),
        "maximal_drawdown": float(drawdowns["maximal_drawdown"]),
        "relative_drawdown": float(drawdowns["relative_drawdown"]),

        "profit_factor": float(win_row.profit_size.sum() / abs(lose_row.profit_size.sum())),
        "recovery_factor": recovery_factor
        }

        filled_none_summary_dict = {k : None if str(v) == "nan" and np.isnan(v) else v for k, v, in summary_dict.items()}
        self.db_client.session.bulk_update_mappings(BacktestSummary, [filled_none_summary_dict])


    def calc_recovery_factor(self, maximal_drawdown, total_return):
        return 0 if maximal_drawdown == 0 else total_return / maximal_drawdown


    def get_row_with_condition(self, profit_status=None, order_type=None):
        profit_status_condition = (self.transaction_logs_df["profit_status"] == profit_status)
        order_type_condition = (self.transaction_logs_df["order_type"] == order_type)

        if profit_status is not None and order_type is not None:
            return self.transaction_logs_df[(profit_status_condition)  & (order_type_condition)]
        elif profit_status is not None and order_type is None:
            return self.transaction_logs_df[(profit_status_condition)]
        elif profit_status is None and order_type is not None:
            return self.transaction_logs_df[(order_type_condition)]
        else:
            return None

    def calc_total_return_percentage(self, transaction_logs_df):
        if transaction_logs_df.iloc[-1].current_balance > 0:
            return float(100 * (transaction_logs_df.iloc[-1].current_balance / self.tradingbot.initial_balance))
        else:
            return float(-100 * (abs(transaction_logs_df.iloc[-1].current_balance) + self.tradingbot.initial_balance)\
                                                     / self.tradingbot.initial_balance)

    def calc_holding_ms(self, row):
        return row["holding_time"].mean().to_pytimedelta() if row.empty is not True else timedelta(seconds=0)


    def build_drawdowns(self):
        if self.transaction_logs_df.current_balance.min() < 0:
            absolute_drawdown = self.tradingbot.initial_balance + self.transaction_logs_df.current_balance.min() 
        else:
            absolute_drawdown = self.tradingbot.initial_balance - self.transaction_logs_df.current_balance.min() 

        current_drawdown = 0
        current_relative_drawdown = 0

        max_balance = self.tradingbot.initial_balance

        maximal_drawdown = 0
        relative_drawdown = 0

        for log in self.transaction_logs_df.itertuples():
            if max_balance < log.current_balance:
                max_balance = log.current_balance
            else:

                if log.current_balance > 0:
                    current_drawdown = max_balance - log.current_balance
                else:
                    current_drawdown = max_balance + log.current_balance

                current_relative_drawdown = (abs(current_drawdown) / max_balance)*100

                if maximal_drawdown < current_drawdown:
                    maximal_drawdown = current_drawdown

                if relative_drawdown < current_relative_drawdown:
                    relative_drawdown = current_relative_drawdown
        
        return {
            "absolute_drawdown" : absolute_drawdown,
            "maximal_drawdown": maximal_drawdown,
            "relative_drawdown" : relative_drawdown
        }


    def build_consecutive(self, profit_status):
        current_start_index = 0
        current_end_index = 0

        max_start_index = 0
        max_consecutive = 0
        max_end_index = 0

        consective_flag = False

        consecutive_win_lose_entries = []

        profit_status_df = self.transaction_logs_df.loc[:,["profit_status"]]
        profit_status_np = profit_status_df.to_numpy(copy=True)

        # for loop
        for row_id, row in enumerate(profit_status_np):
            if row[0] == profit_status:
                if consective_flag is False:
                # consecutive count start
                    current_start_index = row_id
                    consective_flag = True
            else:
                if consective_flag:
                    current_end_index = row_id

                    if max_consecutive <= current_end_index - current_start_index:
                        max_start_index = current_start_index
                        max_end_index = current_end_index - 1
                        max_consecutive = current_end_index - current_start_index

                    consecutive_win_lose_entries.append(current_end_index - current_start_index)
                    consective_flag = False

        if consecutive_win_lose_entries:
            consecutive_max_entry = np.max(consecutive_win_lose_entries)
            consecutive_average_entry = np.mean(consecutive_win_lose_entries)
        else:
            consecutive_max_entry = 0
            consecutive_average_entry = 0

        return_hash = {
            "consecutive_df": self.transaction_logs_df.loc[max_start_index:max_end_index],
            "consecutive_max_entry": int(consecutive_max_entry),
            "consecutive_average_entry": float(consecutive_average_entry)
        }

        return return_hash

    def init_summary(self):
        summary = BacktestSummary().__table__
        init_summary = {
            "bot_name": self.tradingbot.default_params["bot_name"],
            "initial_balance": self.tradingbot.initial_balance,
            "account_currency": self.tradingbot.account_currency
        }

        self.db_client.connector.execute(summary.insert().values(init_summary))
        # [FIXME] only for single task processing, unable to parallel process
        return int(self.db_client.get_last_row("backtest_summary").index.array[0])

    def insert_params_management(self, summary_id):
        backtest_management = self.backtest_management_table()
        self.tradingbot.combined_params["backtest_summary_id"] = int(summary_id)

        self.db_client.connector.execute(backtest_management.insert().values(self.tradingbot.combined_params))