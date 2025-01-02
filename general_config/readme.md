# 通用設定

這裡是全系統通用設定檔規範，在各模組啟動時均會參照此類設定檔

## 標的代碼

> 整體為二節編碼, {交易所代碼}.{商品代碼}, e.g. TWE.2330 表示台積電 (在集中交易市場, 因此是 TWE); CME.MYM202501 表示 2025/01 到期的微型道瓊期貨合約

> 在開發各券商 MarketAPI, TradeAPI 應參考此表分別建立映射關係設定檔，以便在系統內部使用統一標的代碼

- 交易所

  | Exchange  | Description |
  | :---: | :---------- |
  | TWE | 台灣證交所 |
  | TWO | 台灣櫃買上櫃 |
  | ESB | 台灣櫃買興櫃 |
  | SSE | 上海證交所 |
  | SZE | 深圳證交所 |
  | BJE | 北京證交所 |
  |     |           |
  | TWF | 台灣期交所 |
  | HKEX | 香港聯交所 |
  | JPX | 日本交易所 |
  | KRX | 韓國交易所 |
  | CBOT | 芝加哥期交所 |
  | CME | 芝商所 |
  | NYBOT | 紐約期交所 | 
  | NYMEX | 紐商所 |
  | CFE | 芝加哥期權交易所 |
  | EUREX | 歐洲期交所 |

- 商品 (搭配交易所出現)
  > 此為 SDK 直接向策略公開的常用期貨代碼, 不為各券商直接使用的代碼, 在行情/交易端應根據各券商實作 Mapping

  - 期貨季/月合約編碼方式均為 {Symbol}{到期年月}, e.g. TX202503 -> 台指期 2025/03 到期合約
  - 期貨週合約編碼方式為 (A)BC (E)FG (I)JK (U)VW 對應 12 個月份 (英文母音做各季首月)，並由數字對應月中周次, e.g. TX2025C3 -> 台指期 2025/03 W3 到期合約
  - 選擇權合約編碼方式為 {履約價}{C/P} 並附加於對應期貨合約之後, e.g. TX2025C3-24000P -> 台指期 2025/03 W3 到期合約, 履約價 24,000 Put

  - 當合約 Symbol 含有 "-" 時，為選擇權報價，其後附加履約價及 C/P 資訊；若未含有 "-" 時，長度 > 6 且尾部為 6 位數字時為期貨，否則為證券或加密貨幣對


  | Exchange.Symbol | Description | Timezone |
  | :-------------: | :---------- | :------: |
  | TWF.TX | 台指期 (大台) | Asia/Taipei |
  | TWF.MTX | 台指期 (小台) | Asia/Taipei |
  | JPX.225M | 迷你日經 225 | Asia/Tokyo |
  | JPX.TPXM | 小型東證 | Asia/Tokyo |
  | EUREX.FDXS | 微型德 DAX | Etc/GMT-2 |
  | EUREX.FSXE | 微型歐盟藍籌 50 | Etc/GMT-2 |
  | CBOT.ZN | 10 年期美債 | US/Eastern |
  | CBOT.ZT | 2 年期美債 | US/Eastern |
  | CBOT.MYM | 微型道瓊 | US/Eastern |
  | CME.MES | 微型標普 | US/Eastern |
  | CME.MNQ | 微型那指 | US/Eastern |
  | CME.M2K | 微型羅素 2000 | US/Eastern |
  | NYBOT.MME | 小新興市場 | US/Eastern |
  | CME.M6B | 微型英鎊 | US/Eastern |
  | CME.M6A | 微型澳幣 | US/Eastern |
  | NYBOT.DX | 美元指數 | US/Eastern |
  | NYMEX.MHG | 微型高級銅 | US/Eastern |
  | NYMEX.SIL | 微型白銀 | US/Eastern |
  | NYMEX.MGC | 微型黃金 | US/Eastern |
  | NYMEX.MCL | 微型輕原油 | US/Eastern |
  | CFE.VXM | 小 VIX | US/Eastern |


## 標的白名單

### 指定交易櫃台可接受下單的標的

每套交易櫃台只能接受一組 KeyValue 設定, 寫多無用哦！

```python
# dict(櫃台別名, [可交易標的]), 應與啟動參數 instance_id 對應
{
    "KGI_TS01": [
        # 當僅有單節編碼時, 應視為 {Exchange}.* 的效力, 為全交易所標的通用設定
        "TWE",
        "TWO",
        "ESB"
    ]
}

# 或是你想交易的是期貨 / 選擇權, 那可以這樣寫 (不用寫出合約月份, 只需要寫到 Symbol 即等效於 {Exchange}.{Symbol}*)
{
    "KGI_TF02": [
        "NYBOT.DX",
        "CBOT.ZN",
        "CBOT.ZT",
        "CME.MES",
        "CME.MNQ"
    ]
}
```

### 指定行情終端訂閱的標的

行情終端根據自己被指派的 instance_id 參考須訂閱的行情資訊

```python
{
    "KGI_MS01": [
        "TWE.2330",
        "TWE.0050",
        "TWE.2603"
    ],
    # 訂閱行情有限制數量, 所以必須明確要訂閱的合約月份, 如果是選擇權還必須要指定履約價及 Call/Put Side (我個人是不建議在一個策略進程中同時做海期又做台指選擇權啦, 你可以考慮分開來單做海期與單做台指 + 選擇權, 避免性能瓶頸)
    "KGI_MF02": [
        "NYBOT.DX202503",
        "NYBOT.MME202503",
        "NYMEX.MGC202502",
        "NYMEX.MHG202503",
        "NYMEX.SIL202503"
    ],
    "KGI_MF03": [
        "JPX.225M202501",
        "JPX.225M202503",
        "JPX.TPXM202501",
        "JPX.TPXM202503"
    ]
}


```

## 標的詳情

指定標的：開收盤時間 / 時區資訊、休市資訊、進位制、跳動點、合約規模

開/休市時間會基於各分層設定 Overwriting, 分層為:

- by Exchange: 基於一整個交易所進行設定, 其下所有 Symbol 通用, 常見於證券交易所或少數只有單一類型商品的期貨交易所 (e.g. 台灣期交所, 別跟我槓他有別的合約, 他並! 沒! 有! 其他都是死魚合約啦)
- by Symbol: 基於單一商品進行設定, 其下各月份合約通用 (e.g. NYBOT MME 與 DX 在假日開/收盤時間不同, 因標的類型不同)

```python
# Overwriting Type
# O: Open adjust, 開市調整
# C: Close adjust, 收盤調整
# SS: Stop start, 休市開始 (e.g. 2025 台指期自 01/23 08:45 開始休市)
# SE: Stop end, 休市結束 (e.g. 2025 台指期休市至 02/03 05:00)

{
    # 當僅有單節編碼時, 應視為 {Exchange}.* 的效力, 為全交易所標的通用設定
    "TWE": {
        "Currency": "TWD",
        "Denominator": 1,
        # 證券不使用保證金制度, 標記為 None
        "Margin": None,
        # 台股整張為 1,000 股 (不接受零股交易)
        "Size": 1000,
        # 台股 / 日股 Tick Size 會因報價大小而變動, 此處為 dict | decimal 型別, 若為 decimal 型別則無論報價大小都保持一致 (美股 / 中國 A 股)
        "Tick": {
            0: 0.01,
            10: 0.05,
            50: 0.1,
            100: 0.5,
            500: 1,
            1000: 5
        }
        "Timezone": "Asia/Taipei",
        "BusinessDays": [
            [1, 9, 0], [5, 13, 30]
        ]
        "OpeningHours": [
            [9, 0, 0], [13, 30, 0]
        ]
        "OpeningOverwrite": [
            ["SS", "1", "1", "2025", "3", "9", "0"],
            ["SE", "1", "1", "2025", "3", "13", "30"],
            ["SS", "23", "1", "2025", "4", "9", "0"],
            ["SE", "31", "1", "2025", "5", "13", "30"]
        ]
    },
    "NYBOT.DX": {
        # 報價幣別
        "Currency": "USD", 
        # 報價分母
        "Denominator": 1,
        # 原始保證金
        "Margin": 1857,
        # 合約規模 (乘數)
        "Size": 1000,
        # 跳動點 (因此 1000 * 0.005 = 5, 即每一跳動點 5 美元)
        "Tick": 0.005,
        # 開盤時區 (使用 Python 美東時區, 因為夏令差 12 小時較容易記憶, 並且與美中時區共用冬夏令時設定, 若其他模組可能需要建立時區映射表)
        "Timezone": "US/Eastern",
        # 每周開/收盤時間, 格式 [[每周開盤時間], [每周收盤時間]], 時間格式 [Weekday(0-6 -> Sun-Sat), Hour, Minute]
        "BusinessDays": [
            [0, 18, 0], [5, 17, 0]
        ],
        # 格式 [[當節開盤時間], [當節收盤時間]], 時間格式 [Hour, Minute, Second, Microsecond]
        "OpeningHours": [
            [[20, 0, 0, 0], [23, 59, 59, 999999]],  # 第一節開/收盤時間 (因為跨日, 自動分為兩節)
            [[0, 0, 0, 0], [17, 0, 0, 0]]  # 第二節開/收盤時間
        ],
        # 格式 [Overwriting Type, Day, Month, Year, Weekday(0-6 -> Sun-Sat), Hour, Minute]
        # 下方為 NYBOT.DX 2024 聖誕節 ~ 2025 新年開/休市設定 Overwriting, 以下均為 "美東時間(夏令 -12H, 冬令 -13H)"
        "OpeningOverwrite": [
            ["O", "?", "*", "*", "0", "18", "0"],  # 美元指數會在每週日 18:00 提前開盤 (平常是 20:00 開隔日盤)
            ["C", "24", "12", "2024", "2", "13", "45"],  # 在 12/24 提早至 13:45 收盤
            ["SS", "24", "12", "2024", "2", "18", "0"],  # 在 12/24 18:00 開始休市
            ["SE", "25", "12", "2024", "3", "17", "0"],  # 在 12/25 17:00 結束休市, 換言之 18:00 將正常開隔日盤
            ["SS", "31", "12", "2024", "2", "18", "0"],
            ["SE", "1", "1", "2025","3", "17", "0"]
        ]
    },
    "CBOT.ZN": {
        "Currency": "USD",
        # 報價分母, 十年期美債是以 1/64 報價, 最終影響 TradeAPI 給出報價的格式
        "Denominator": 64,
        "Margin": 2200,
        "Size": 1000,
        # 策略委託時的最小遞進量為十進制 0.015625, TradeAPI 將根據此值轉換為報價格式
        "Tick": 0.015625,
        "Timezone": "US/Eastern",
        "BusinessDays": [
            [0, 18, 0], [5, 17, 0]
        ],
        "OpeningHours": [
            [[18, 0, 0, 0], [23, 59, 59, 999999]],
            [[0, 0, 0, 0], [17, 0, 0, 0]]
        ],
        "OpeningOverwrite": [
            ["C", "24", "12", "2024", "2", "13", "15"],
            ["SS", "24", "12", "2024", "2", "18", "0"],
            ["SE", "25", "12", "2024", "3", "17", "0"],
            ["SS", "31", "12", "2024", "2", "18", "0"],
            ["SE", "1", "1", "2025", "3", "17", "0"]
        ]
    }
}
```