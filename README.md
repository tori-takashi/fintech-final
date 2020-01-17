# fintech-final

Fintech Final Project for Group 4

## installation

### install Anaconda

Follow this installation guide by official
[Anaconda](https://docs.anaconda.com/anaconda/install/)

### install MySQL

for backtest

1. install MySQL server

   `$ sudo apt-get install -y mysql-server`

   `$ mysql --version`

   ```
   mysql Ver 14.14 Distrib 5.7.28, for Linux (x86_64) using EditLine wrapper
   ```

   `$ sudo service mysql start`

2. login as root and create database

   `$ sudo mysql -uroot`

   `mysql> CREATE DATABASE tradingbot;`

3. user settings

   `mysql> CREATE USER 'tradingbot'@'localhost' IDENTIFIED BY 'password';`

   `mysql> GRANT ALL ON tradingbot.* TO 'tradingbot'@'localhost' IDENTIFIED BY 'password';`

4. set config
   set conig.ini

5. change character set for twitter

   `$ mysql --help | grep my.cnf`

   then add to the global option file to

   ```
   [mysqld]
    character-set-server=utf8mb4

   [client]
    default-character-set=utf8mb4
   ```

6. restart mysql deamon

   `$ sudo service mysql restart`

7. update settings for future

log in to mysql then

`mysql > ALTER DATABASE 【DB 名】 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci`

### install influxdb

for real environment

1. install and configuration influx db

   [influxdb install documentation](https://docs.influxdata.com/influxdb/v1.7/introduction/installation/)

   [influxdb setup](http://hassiweb-programming.blogspot.com/2018/10/how-to-use-python-library-for-influxdb.html)

2. add admin user

   `$ influx`

   `> CREATE USER admin WITH PASSWORD 'password' WITH ALL PRIVILEGES`

   `$ exit`

3. add tradingbot user and permission

   `$ influx -precision rfc3339 -username admin -password <password>`

   `> CREATE USER tradingbot WITH PASSWORD 'password'`

   `> GRANT ALL ON tradingbot TO tradingbot`

   `> SHOW GRANTS FOR "tradingbot"`

   ```
    database   privilege
    --------   ---------
    tradingbot ALL PRIVILEGES
   ```

   `$ exit`

4. set config
   set conig.ini

### intall talib

1. follow instructions like below to install talib.

   [instructions to download talib](https://sachsenhofer.io/install-ta-lib-ubuntu-server/)

Need to install talib to your system.

[TALib file](https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/)

2. take note for talib installation path.

   `$ sudo find / -name libta_lib.so.0`

   ```
   /usr/local/lib/libta_lib.so.0
   ```

Because probably you will face an error like below when you try to import talib.

`ImportError: libta_lib.so.0: cannot open shared object file: No such file or directory`

3. So open profile then add path to talib.

   `$ vim ~/.profile` or your bash profile.

4. From the result of searching lib location, append it to tail of `profile`.

   `export LD_LIBRARY_PATH="/usr/local/lib"`

5. Then update `profile`

   `$ source ~/.profile`

### install Grafana

1. install and configuration
   [Grafana official page](https://grafana.com/grafana/download?platform=linux)

```
wget https://dl.grafana.com/oss/release/grafana_6.5.2_amd64.deb
sudo dpkg -i grafana_6.5.2_amd64.deb
```

2. access to local server

```
$ service grafana-server start
$ service grafana-server status
```

Then open your browser and access to http://localhost:3000/

Initial user id and password are

```
username: admin
password: admin
```

4. add influxdb as data source
   If you success in save and test, then move on the next step.

5. create graph

### install python packages and build database

install packages like below.

Beforehand of installation, update setuptools.

If you're using anaconda, please replace `pip` to `conda`

`$ sudo pip install -U setuptools`

`$ pip install ccxt pandas numpy sklearn ta-lib sqlalchemy influxdb alembic PyMySQL websocket tweepy`

### settings to alembic.ini

edit alembic.ini

`sqlalchemy.url = mysql+pymysql://tradingbot:<password>@localhost/tradingbot`

### build database

`$ python3 tradingbot/build_dataset.py`

If you move into tradingbot directory, it would be failed due to unable to read config.ini.

`$ jupyter notebook`

You might be faced with this error at first execution, it's a bug in sqlalchemy so please ignore and run again.

```
sqlalchemy.exc.ArgumentError: Could not locate any simple equality expressions involving locally mapped foreign key columns
 for primary join condition 'bottom_trend_follow_backtest_management.backtest_summary_id = backtest_summary.id' on
 relationship BacktestManagement.backtest_summary.  Ensure that referencing columns are associated with a ForeignKey or
 ForeignKeyConstraint, or are annotated in the join condition with the foreign() annotation. To allow comparison operators
 other than '==', the relationship can be marked as viewonly=True.
```

### nltk setting

`$ python3 nltk_download.py`

## TALib Error

If you face error of talib importing, please try to reimport your bash profile which is setting the path of talib

## credits

tuned_bitmex_websocket.py was downloaded from [here](https://note.mu/motofumimikami/n/n3baccdc81674)

tuned_bitmex_websocket is based on [bitmex-ws](https://github.com/BitMEX/api-connectors/tree/master/official-ws/python)

sentiment analysis dictionary in investment [NTUSD-Fin: A Market Sentiment Dictionary for Financial Social Media Data Applications](http://nlg.csie.ntu.edu.tw/nlpresource/NTUSD-Fin/)

## Sentiment Analysis Materials

[Sentiment Analysis with Python (Finance) – A Beginner’s Guide](https://algotrading101.com/learn/sentiment-analysis-with-python-finance/)
[Algorithmic Trading using Sentiment Analysis on News Articles](https://towardsdatascience.com/https-towardsdatascience-com-algorithmic-trading-using-sentiment-analysis-on-news-articles-83db77966704)
[Financial Sentiment Analysis Part II – Sentiment Extraction](http://francescopochetti.com/financial-blogs-sentiment-analysis-part-crawling-web/)
[NLP2018SPRING](https://github.com/thtang/NLP2018SPRING/blob/master/project1/fine_grained.py)

### dictionary

[https://github.com/nunomroliveira/stock_market_lexicon](https://github.com/nunomroliveira/stock_market_lexicon)
[Extending the Loughran and McDonald Financial Sentiment Words List from10-K Corporate Fillings using Social Media Texts](http://lrec-conf.org/workshops/lrec2018/W13/pdf/1_W13.pdf)
[Loughran and McDonald Sentiment Word Lists](https://sraf.nd.edu/textual-analysis/resources/#LM%20Sentiment%20Word%20Lists)
[NRC Word-Emotion Association Lexicon (aka EmoLex)](http://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm)
[NTUSD-Fin: A Market Sentiment Dictionary for Financial Social Media Data Applications](http://qcl.tw/~hhhuang/docs/fnp2018.pdf)

### Papers

[Using social media and machine learning to predict financial performance of a company](https://uu.diva-portal.org/smash/get/diva2:955799/FULLTEXT01.pdf)
[Simplifying Sentiment Analysis using VADER in Python (on Social Media Text)](https://medium.com/analytics-vidhya/simplifying-social-media-sentiment-analysis-using-vader-in-python-f9e6ec6fc52f)
[DATA AND TEXT MINING OF FINANCIAL MARKETS USING NEWS AND SOCIAL MEDIA](https://studentnet.cs.manchester.ac.uk/resources/library/thesis_abstracts/MSc12/FullText/Han-Zhichao-fulltext.pdf)
[How to Create and Backtest Trading Strategy on Twitter Sentiments](https://devexperts.com/blog/how-to-create-and-backtest-trading-strategy-on-twitter-sentiments/)
