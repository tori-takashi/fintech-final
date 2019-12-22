# fintech-final

Fintech Final Project for Group 4

## installation

### install influxdb

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
   `$ exit`

### intall talib

1. follow instructions like below to install talib.
   [instructions to download talib](https://sachsenhofer.io/install-ta-lib-ubuntu-server/)

Need to install talib to your system.
[TALib file](https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/)

2. take note for talib installation path.
   `$ sudo find / -name libta_lib.so.0`
   > I got `/usr/local/lib/libta_lib.so.0`

Because probably you will face an error like below when you try to import talib.
`ImportError: libta_lib.so.0: cannot open shared object file: No such file or directory`

3. So open profile then add path to talib.
   `$ vim ~/.profile` or your bash profile.

4. From the result of searching lib location, append it to tail of `profile`.
   `export LD_LIBRARY_PATH="/usr/local/lib"`

5. Then update `profile`
   `$ source ~/.profile`

### install python packages

install packages like below.
Beforehand of installation, update setuptools.
If you're using anaconda, please replace `pip` to `conda`

`$ sudo pip install -U setuptools`
`$ pip install ccxt pandas ta-lib sqlalchemy influxdb`

### create csv

`$ python3 build_dataset.py`

## Error

If you face error of talib importing, please try to reimport your bash profile which is setting the path of talib.

## credits

tuned_bitmex_websocket.py was downloaded from [here](https://note.mu/motofumimikami/n/n3baccdc81674)
tuned_bitmex_websocket is based on [bitmex-ws](https://github.com/BitMEX/api-connectors/tree/master/official-ws/python)
