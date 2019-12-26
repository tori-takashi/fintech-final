from configparser import SafeConfigParser
import ccxt
import sys
import os
import pathlib
from .config import Config


class ExchangeClient:
    #################################################
    #               instance variables
    #
    # client                 client dict
    # config(private)        exchange_config data
    #
    # return ccxt client after initialized
    #################################################

    def __init__(self, name, config_path):
        self.name = name

        self.config = Config(config_path).config
        self.client = self.establish_connection_to_exchange()

    # append name and establish function if you added exchanges
    def establish_connection_to_exchange(self):
        if self.name == "bitmex":
            return self.bitmex_establish_connection()

    # connect to bitmex
    def bitmex_establish_connection(self):
        return ccxt.bitmex({
            "apiKey": self.config['bitmex']['apiKey'],
            "secret": self.config['bitmex']['secret']
        })
