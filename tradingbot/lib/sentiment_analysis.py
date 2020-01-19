# credit https://github.com/thtang/NLP2018SPRING/blob/master/project1/fine_grained.py

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
import os
import numpy as np

import json


class SentimentAnalysis:
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()

        # load NTUSD-FIN
        with open(os.path.dirname(__file__) + "/NTUSD-Fin/NTUSD_Fin_word_v1.0.json", "r") as f:
            data = f.read()
            NTUSD = json.loads(data)
        self.word_sent_dict = {}
        for i in range(len(NTUSD)):
            self.word_sent_dict[NTUSD[i]["token"]
                                ] = NTUSD[i]["market_sentiment"]

        self.stop_words = set(stopwords.words('english'))
        self.stop_words |= set(
            ['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}', '@', '#'])

    def calc_vader_scores(self, sentence):
        sentence = self.remove_stopwords(sentence)
        return self.vader_analyzer.polarity_scores(" ".join(sentence))

    def calc_ntusd_scores(self, sentence):
        sentence = self.remove_stopwords(sentence)
        market_sentiment = np.array([self.convert_to_ntusd_market_sentiment(
            word) for word in sentence if self.convert_to_ntusd_market_sentiment(word) is not None])
        mean = market_sentiment.mean()
        return mean if not np.isnan(mean) else None

    def convert_to_ntusd_market_sentiment(self, word):
        return self.word_sent_dict.get(word)

    def remove_stopwords(self, data):
        return [word for word in data.lower().split()
                if word not in self.stop_words]
