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

`$ pip install ccxt pandas numpy sklearn ta-lib sqlalchemy influxdb alembic PyMySQL websocket`

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

## Error

If you face error of talib importing, please try to reimport your bash profile which is setting the path of talib

## credits

tuned_bitmex_websocket.py was downloaded from [here](https://note.mu/motofumimikami/n/n3baccdc81674)

tuned_bitmex_websocket is based on [bitmex-ws](https://github.com/BitMEX/api-connectors/tree/master/official-ws/python)
