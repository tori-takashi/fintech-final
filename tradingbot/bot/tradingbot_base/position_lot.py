class PositionLot:
    def __init__(self, tradingbot, position_management):
        self.tradingbot = tradingbot
        self.position_management = position_management

    def calculate_lot(self, row):
        lot_proportion = self.tradingbot.calculate_specific_lot(row)
        lot = (row.close * self.position_management.current_balance) * \
            lot_proportion
        return lot
