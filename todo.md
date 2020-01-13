# Todo

本番環境のキーを取得
本番用メソッドの用意
初期ではテストネットで

- 最新のデータを取得する
  - get ohlcv
- 今のテクニカル指標を計算する
  - calc metrics
  - calc ta
  - db に書き込み
- 例外や価格のすべりの処理
  - 例外の記述
  - ずらし法の実装(デフォルトで設定できそうなので backtest management などにパラメータの追加が必要そう、後でやる)
- 1 分おきに ohlcv データとテクニカル指標を更新する
- シグナルに応じて注文を出す、決済する

  - ccxt で注文を出す
  - 注文を管理する
  - 注文を決済する

  - OHLCV_data

    - ohlcv
    - 取引所名
    - 資産名
    - 時刻

  - WS data

    - あとで

  - 注文を出した時には

    - transaction log と共通のものとしては
      - 交換所の名前
      - 資産の名前
      - エントリー時刻
      - order type
      - 判断価格
      - レバレッジ
      - ロット
    - を記録し、異なるものとしては

      - bot 名
      - その bot のパラメータから作ったタグ、例えば(bottom_trend_follow_1_5_3_1_1_0)
        - timeframe1, bottom5, middle3, top1, close_position_on_do_nothing=True, inverse_trading=False
          にデフォルトオプションを加えた形
        - 仕様として明文化しなければならなそう
        - row_open, close にのっけてある
      - order status(open close pass)
      - トレンド(uptrend downtrend)
        - row_open にのってる
      - 実際のエントリー時刻
      - 実際のエントリー価格
        　- 実際のエントリーと判断価格の差 = 滑りの幅
      - 滑りの幅
      - 滑りの総秒数
      - 発生した滑りの回数
      - 0.25%の maker 手数料のうちの何%を使ったか
      - 手数料の大きさ

      - 注文を出す判断の時点でのテクニカル指標
        を記録する

  - 注文を閉じた時には

    - transaction log と共通のものとしては
      - クローズ時刻
      - クローズ価格
      - 取った値幅
      - 値幅のパーセンテージ
      - 総利益
      - 手数料
      - order type
      - gross profit
      - profit size
      - profit status
      - profit percentage
      - current balance
      - order status=closed
    - を記録し、異なるものとしては

      - 実際のエントリー時刻
      - 実際のエントリー価格
      - 実際のエントリーと判断価格の差
      - 滑りの幅
      - 滑りの総秒数
      - 発生した滑りの回数
      - 0.25%の手数料のうち何%を使ったか
      - 手数料の大きさ

      - 0.05%の取引手数料を加味した総取引手数料

    を記録する

通知

- 上の記録のうち、エントリ時刻、利確、損切り。エントリはいつ、どういう判断で、どれくらいの注文を出したか
- 1 時間、1 日、1 週間、1 ヶ月おきのの口座情報とトレードサマリーを LINE の別のグループで通知する

influxdb

### pass と open と close のテクニカル指標比較できるように measurement 追加する

row を dict にしてつないでやればいい
