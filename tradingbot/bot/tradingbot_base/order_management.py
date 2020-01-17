from datetime import datetime
from .order_price_calculator import OrderPriceCalculator


class OrderManagement:
    def __init__(self, position_management):
        self.position_management = position_management
        self.tradingbot = self.position_management.tradingbot
        self.order_price_calculator = OrderPriceCalculator(self.tradingbot)

    def send_order(self):
        asset_name = self.position_management.position.asset_name
        # [FIXME] close all lot in the position
        lot = self.position_management.position.lot
        side = self.convert_order_type(
            self.position_management.position.order_type, self.position_management.position.order_status)

        order_price = self.order_price_calculator.calculate_order_price(
            self.position_management.position, self.position_management.position.order_method)
        self.send_order_notification(order_price)

        if self.position_management.position.order_method == "limit":
            return self.tradingbot.exchange_client.client.create_order(asset_name, self.position_management.position.order_method,
                                                                       side, lot, round(order_price, 1), params={'execInst': 'ParticipateDoNotInitiate'})
        elif self.position_management.position.order_method == "market":
            return self.tradingbot.exchange_client.client.create_order(asset_name, self.position_management.position.order_method, side, lot)

    def convert_order_type(self, order_type, order_status):
        if (order_type == "long" and order_status == "pass") or (order_type == "short" and order_status == "open"):
            return "buy"
        elif (order_type == "short" and order_status == "pass") or (order_type == "long" and order_status == "open"):
            return "sell"

    def send_order_notification(self, order_price):
        position_details = self.position_management.position.order_type + " order at: $" + str(round(order_price, 2)) + \
            " lot: $" + str(self.position_management.position.lot) + " leverage: " + \
            str(self.position_management.position.leverage) + "x"

        if self.position_management.position.order_status == "pass":
            self.tradingbot.line.notify("try entry " + position_details)
        elif self.position_management.position.order_status == "open":
            self.tradingbot.line.notify(
                "try closing " + position_details)

    def cancel_failed_order(self, id):
        try:
            self.tradingbot.exchange_client.client.cancel_order(id)
        except Exception as e:
            self.tradingbot.line.notify(e)
            self.tradingbot.line.notify("order was deleted. retry")

    def is_position_opened(self, row, order_start_time, attempted_time, order_info):
        if order_info["status"] == "closed":
            self.position_management.position.order_status = "open"
            self.tradingbot.line.notify("entry order was successfully opened")
            open_log = {
                "entry_price": order_info["price"],
                "entry_attempt_time": attempted_time,
                "order_method": "limit"
            }
            self.position_management.position.set_open_log(open_log)
            return self.position_management.position

        elif order_info["status"] == "open":    # order failed
            self.tradingbot.line.notify(
                "entry order failed, retrying. time:" + str(attempted_time))
            self.cancel_failed_order(order_info["id"])
            return self.position_management.position

    def is_position_closed(self, row, order_start_time, attempted_time, order_info):
        position = self.position_management.position
        if order_info["status"] == "closed":  # order sucess
            updated_balance = self.tradingbot.exchange_client.client.fetch_balance()[
                "BTC"]["total"]

            # notify
            self.tradingbot.line.notify("order was successfully closed.\n \
                current_balance: " + str(round(updated_balance, 5)) + "BTC\nasset moving : " +
                                        str(round((updated_balance - position.current_balance) / position.current_balance*100, 5)) + "%")

            # send log to influxdb
            self.create_close_transaction_log_for_real(row, order_start_time,
                                                       updated_balance, attempted_time, order_info)

            # update current balance
            self.current_balance = updated_balance
            return position

        else:  # order Failed
            self.tradingbot.line.notify(
                "position closing failed. retry. total attempted time:" + str(attempted_time))
            self.cancel_failed_order(order_info["id"])
            return position

    def create_close_transaction_log_for_real(self, row, order_close_time, updated_balance, attempted_time, order_info):
        close_params = {
            "close_position_id": order_info["id"],
            "close_judged_price": row.close,
            "close_judged_time": row.index,
            "close_price": order_info["price"],
            "close_attempt_time": attempted_time,
            "close_attempt_period": datetime.now() - order_close_time,
            "close_order_method": "limit",
            "current_balance": updated_balance
        }

        self.position_management.position.set_close_log(close_params)
        self.tradingbot.db_client.influx_raw_connector.write_points(
            [self.position_management.position.get_combined_log()])
