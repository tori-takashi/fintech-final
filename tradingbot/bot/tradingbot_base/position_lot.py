class PositionLot:
    def __init__(self, tradingbot):
        self.tradingbot = tradingbot

    def calculate_lot(self, row):
        lot = self.tradingbot.calculate_specific_lot(row)
        return lot
