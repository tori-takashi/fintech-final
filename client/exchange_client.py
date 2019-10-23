from configparser import SafeConfigParser
import ccxt
import sys
import os


class ExchangeClient:
    #################################################
    #               instance variables
    #
    # client                 client dict
    # config(private)        exchange_config data
    #
    # return ccxt client after initialized
    #################################################

    def __init__(self, name):
        self.config = SafeConfigParser()

        # config.ini should be same place to executing file
        self.config.read("config.ini")
        self.client = self.establish_connection_to_exchange(name)

    # append name and establish function if you added exchanges
    def establish_connection_to_exchange(self, name):
        if name == "bitmex":
            return self.bitmex_establish_connection()

    # connect to bitmex
    def bitmex_establish_connection(self):
        return ccxt.bitmex({
            "apiKey": self.config['bitmex']['apiKey'],
            "secret": self.config['bitmex']['secret']
        })
