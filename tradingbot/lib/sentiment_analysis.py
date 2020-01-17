from nltk.sentiment.vader import SentimentIntensityAnalyzer


class SentimentAnalysis:
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()

    def calc_vader_scores(self, sentence):
        return self.vader_analyzer.polarity_scores(sentence)
