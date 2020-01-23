# ver. 1 (1min)

L2 orderbook の平均処理時間が長い
max も長い

幅絞りあり、10 件ごとに更新していた

## log

total timeframes
132
average downloading pace
0.45454545454545453
total l1 rows
last 8
buy 8
sell 8
mid 8
timestamp 8
dtype: int64
total l2 rows
symbol 2260245
side 2260245
size 2260245
price 2260245
timestamp 2260245
dtype: int64
total recent trades rows
timestamp 5518
symbol 5518
side 5518
size 5518
price 5518
tickDirection 5518
trdMatchID 5518
grossValue 5518
homeNotional 5518
foreignNotional 5518
dtype: int64
=l1 orderbook=
average processing time: 7.347560975609755e-05
max processing time: 0.002475

```
=l2 orderbook=
average processing time: 0.35348613414634145
max processing time: 0.981415
```

=recent trades=
average processing time: 0.004741920731707318
max processing time: 0.021062
===oneloop===
average processing time: 0.3583208353658537
max processing time: 0.992708

# ver 2

依然として l2 の処理時間は 0.3 秒ほどかかっている
最大処理時間は長くなった

幅絞りあり

## log

total timeframes
159
average downloading pace
0.37735849056603776
total l1 rows
last 6
buy 6
sell 6
mid 6
timestamp 6
dtype: int64
total l2 rows
symbol 2363358
side 2363358
size 2363358
price 2363358
timestamp 2363358
dtype: int64
total recent trades rows
timestamp 4367
symbol 4367
side 4367
size 4367
price 4367
tickDirection 4367
trdMatchID 4367
grossValue 4367
homeNotional 4367
foreignNotional 4367
dtype: int64
=l1 orderbook=
average processing time: 7.194240837696336e-05
max processing time: 0.003068
=l2 orderbook=
average processing time: 0.3038610732984293
max processing time: 1.284233
=recent trades=
average processing time: 0.003626753926701571
max processing time: 0.013271
===oneloop===
average processing time: 0.3075800680628273
max processing time: 1.295326

# ver 3

幅絞りあり、100000 件ごとに更新していた
平均処理時間が大幅に低下し、最大処理時間が長くなった。

## log

total timeframes
521
average downloading pace
0.11516314779270634
total l1 rows
last 4
buy 4
sell 4
mid 4
timestamp 4
dtype: int64
total l2 rows
symbol 2457828
side 2457828
size 2457828
price 2457828
timestamp 2457828
dtype: int64
total recent trades rows
timestamp 28719
symbol 28719
side 28719
size 28719
price 28719
tickDirection 28719
trdMatchID 28719
grossValue 28719
homeNotional 28719
foreignNotional 28719
dtype: int64
=l1 orderbook=
average processing time: 3.7091127098321343e-05
max processing time: 0.00392

```
=l2 orderbook=
average processing time: 0.0546304556354916
max processing time: 1.810578
```

=recent trades=
average processing time: 0.007989785371702638
max processing time: 0.067348
===oneloop===
average processing time: 0.06267895323741007
max processing time: 1.859279

# Ver 4

list のリセットを忘れていたのを修正
L2 の最大処理時間が大幅に改善した

## log

total timeframes
498
average downloading pace
0.12048192771084337
total l1 rows
last 2
buy 2
sell 2
mid 2
timestamp 2
dtype: int64
total l2 rows
symbol 100098
side 100098
size 100098
price 100098
timestamp 100098
dtype: int64
total recent trades rows
timestamp 61482
symbol 61482
side 61482
size 61482
price 61482
tickDirection 61482
trdMatchID 61482
grossValue 61482
homeNotional 61482
foreignNotional 61482
dtype: int64
=l1 orderbook=
average processing time: 3.29736564805058e-05
max processing time: 0.003582
=l2 orderbook=
average processing time: 0.02798521812434141
max processing time: 0.45969
=recent trades=
average processing time: 0.02511590727081138
max processing time: 0.101822
===oneloop===
average processing time: 0.05315882086406744
max processing time: 0.492379

# Ver 5

修正後かつ 1 万行ずつ更新

## log

Connected to WS.
init completed
total timeframes
750
average downloading pace
0.08
total l1 rows
last 0
buy 0
sell 0
mid 0
dtype: int64
total l2 rows
symbol 150750
side 150750
size 150750
price 150750
timestamp 150750
dtype: int64
total recent trades rows
timestamp 32353
symbol 32353
side 32353
size 32353
price 32353
tickDirection 32353
trdMatchID 32353
grossValue 32353
homeNotional 32353
foreignNotional 32353
dtype: int64
=l1 orderbook=
average processing time: 3.0436413540713637e-05
max processing time: 5.9e-05
=l2 orderbook=
average processing time: 0.027201735590118938
max processing time: 0.148501
=recent trades=
average processing time: 0.017560637694419033
max processing time: 0.075705
===oneloop===
average processing time: 0.04481746111619397
max processing time: 0.192244

# Ver 6

5000 行ずつ
1 万行のほうが早い

## log

total timeframes
825
average downloading pace
0.07272727272727272
total l1 rows
last 10
buy 10
sell 10
mid 10
timestamp 10
dtype: int64
total l2 rows
symbol 165825
side 165825
size 165825
price 165825
timestamp 165825
dtype: int64
total recent trades rows
timestamp 28797
symbol 28797
side 28797
size 28797
price 28797
tickDirection 28797
trdMatchID 28797
grossValue 28797
homeNotional 28797
foreignNotional 28797
dtype: int64
=l1 orderbook=
average processing time: 4.206751389992057e-05
max processing time: 0.003911
=l2 orderbook=
average processing time: 0.02693637172359015
max processing time: 0.180419
=recent trades=
average processing time: 0.010544405083399523
max processing time: 0.055699
===oneloop===
average processing time: 0.03754410087370929
max processing time: 0.221066

# ver 7

WideLimit なし
激重処理が消えた分データ量が増える
1 行に全部ぶち込むが、csv の最大サイズ 65535 バイト以降は切り捨てられてしまう

## log

total timeframes
1
average downloading pace
60.0
total l1 rows
last 16
buy 16
sell 16
mid 16
timestamp 16
dtype: int64
total l2 rows
0 606
1 606
price 0
side 0
size 0
symbol 0
timestamp 0
dtype: int64
total recent trades rows
timestamp 80404
symbol 80404
side 80404
size 80404
price 80404
tickDirection 80404
trdMatchID 80404
grossValue 80404
homeNotional 80404
foreignNotional 80404
dtype: int64
=l1 orderbook=
average processing time: 5.7153196622436675e-05
max processing time: 0.003548
=l2 orderbook=
average processing time: 0.0194001507840772
max processing time: 0.026069
=recent trades=
average processing time: 0.04280606272617612
max processing time: 0.133959
===oneloop===
average processing time: 0.06228802533172497
max processing time: 0.155219

# ver 8

init completed
total timeframes
122
average downloading pace
0.4918032786885246
total l1 rows
last 2
buy 2
sell 2
mid 2
timestamp 2
dtype: int64
total l2 rows
symbol 1492250
side 1492250
size 1492250
price 1492250
timestamp 1492250
dtype: int64
total recent trades rows
timestamp 14779
symbol 14779
side 14779
size 14779
price 14779
tickDirection 14779
trdMatchID 14779
grossValue 14779
homeNotional 14779
foreignNotional 14779
dtype: int64
=l1 orderbook=
average processing time: 3.932846715328467e-05
max processing time: 0.002507
=l2 orderbook=
average processing time: 0.41929564233576644
max processing time: 0.985436
=recent trades=
average processing time: 0.013735802919708029
max processing time: 0.031122
===oneloop===
average processing time: 0.43309371532846713
max processing time: 1.011091

# ver 9

値幅を 35 に縮小
WideLimit あり
1 回の処理は 2 万件

## log

total timeframes
639
average downloading pace
0.09389671361502347
total l1 rows
last 24
buy 24
sell 24
mid 24
timestamp 24
dtype: int64
total l2 rows
symbol 90098
side 90098
size 90098
price 90098
timestamp 90098
dtype: int64
total recent trades rows
timestamp 66472
symbol 66472
side 66472
size 66472
price 66472
tickDirection 66472
trdMatchID 66472
grossValue 66472
homeNotional 66472
foreignNotional 66472
dtype: int64
=l1 orderbook=
average processing time: 6.89134396355353e-05
max processing time: 0.003865
=l2 orderbook=
average processing time: 0.02703454555808656
max processing time: 0.10992
=recent trades=
average processing time: 0.031224380410022783
max processing time: 0.119762
===oneloop===
average processing time: 0.05835223120728929
max processing time: 0.207553

# Ver 10

しきい値を 2000 に設定

## log

total timeframes
585
average downloading pace
0.10256410256410256
total l1 rows
last 22
buy 22
sell 22
mid 22
timestamp 22
dtype: int64
total l2 rows
symbol 82480
side 82480
size 82480
price 82480
timestamp 82480
dtype: int64
total recent trades rows
timestamp 73434
symbol 73434
side 73434
size 73434
price 73434
tickDirection 73434
trdMatchID 73434
grossValue 73434
homeNotional 73434
foreignNotional 73434
dtype: int64
=l1 orderbook=
average processing time: 6.688557213930348e-05
max processing time: 0.003672
=l2 orderbook=
average processing time: 0.027382251243781096
max processing time: 0.085472
=recent trades=
average processing time: 0.03707065174129354
max processing time: 0.129435
===oneloop===
average processing time: 0.06454326243781094
max processing time: 0.172321

# Ver 11

Recent Trades にも同様の措置をした
widelimit35, 2000, 2000

## log

total timeframes
960
average downloading pace
0.0625
total l1 rows
last 10
buy 10
sell 10
mid 10
timestamp 10
dtype: int64
total l2 rows
symbol 135360
side 135360
size 135360
price 135360
timestamp 135360
dtype: int64
total recent trades rows
timestamp 24124
symbol 24124
side 24124
size 24124
price 24124
tickDirection 24124
trdMatchID 24124
grossValue 24124
homeNotional 24124
foreignNotional 24124
dtype: int64
=l1 orderbook=
average processing time: 3.6757738095238094e-05
max processing time: 0.007572
=l2 orderbook=
average processing time: 0.02523046845238095
max processing time: 0.106158
=recent trades=
average processing time: 0.0002865619047619048
max processing time: 0.031019
===oneloop===
average processing time: 0.025569946428571428
max processing time: 0.106427

# ver 12

並列処理を入れた
データ件数が 0 なのはメモリを共有していないからだが、DB に書き込むだけなので問題なく
csv に書き出せている

## log

total timeframes
0
average downloading pace
No L1 data
total l1 rows
last 16
buy 16
sell 16
mid 16
timestamp 16
dtype: int64
total l2 rows
symbol 0
side 0
size 0
price 0
timestamp 0
dtype: int64
total recent trades rows
timestamp 0
symbol 0
side 0
size 0
price 0
tickDirection 0
trdMatchID 0
grossValue 0
homeNotional 0
foreignNotional 0
dtype: int64
=l1 orderbook=
average processing time: 4.758732978093547e-05
max processing time: 0.004958
=l2 orderbook=
average processing time: 0.02442763291888692
max processing time: 0.057273
=recent trades=
average processing time: 0.0007279046773238602
max processing time: 0.005609
===oneloop===
average processing time: 0.02522134103019538
max processing time: 0.057404

=l1 orderbook=
average processing time: 7.657509157509156e-05
max processing time: 0.009322
=l2 orderbook=
average processing time: 0.025476983516483517
max processing time: 0.056518
=recent trades=
average processing time: 0.0007126434676434677
max processing time: 0.010849
===oneloop===
average processing time: 0.026284813186813187
max processing time: 0.056718
