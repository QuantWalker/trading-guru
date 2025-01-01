# 致各位共同開發者
感謝各位參與這個項目，這個項目因為有了各位的貢獻才能持續茁壯，大家在開發過程中有功能提案或遇到任何問題的話，歡迎在 `GitHub Issues` 上面開啟討論

## SDK 的運行方式
將採用 `Async + Multi-Threading` 方式運行，確保 IO 過程不會影響策略運算

### 為什麼會用到 Multi-Threading
在 Redis pub/sub 或是 Websocket send/listen 的過程中, 給予獨立的線程處理起來比較方便

### 什麼時候用到 Async
未來可能會引用到外部 REST API 資訊, 因此先保留起來, 但這也意味著如果你希望在此基礎上進行二次開發, 你有 Async 的選項可以使用 (你也可以用同步的, httpx.{method} 不做 await 就行)


### 通用 Lib 的選擇
- 關於 REST Request
  > 執行部分 HTTP Request 將使用 Async 方式執行，httpx 是目前最適合的選項

  `httpx`

- 關於時區庫
  > windows 設備須安裝 tzdata 以載入時區資料 (Linux 有自帶的時區資訊)

  `tzdata + ZoneInfo.zoneinfo`

- 關於宣告資料類型
  > pydantic 應該大家都會用, 就選他了, 而且用來載入環境變量也比較方便

  `pydantic, pydantic-settings`

- 關於數值類型
  > 有關價格/數量的欄位, 均須以 numpy f8 類型保存, 因為我們運行過程都會持續用於運算, 正常來說應該使用 decimal.Decimal, 但 Decimal 放在 numpy 裡面的操作實在很受限 (在運算完成後, 發送訂單我們確實會將結果轉型成 decimal.Decimal 再發送)
  
  `numpy f8`

- 關於 dump to JSON 的方式
  > 由於使用 Decimal 類型, 在 dump 時若採用常見的 json.dumps(object, ensure_ascii=False) 會產生錯誤, 所幸 fastapi.encoder 提供了一個 jsonable_encoder 函數可以完美解決這個問題
  
  `fastapi.encoder.jsonable_encoder`

- 關於 Configuration 文件類型
  
  `JSON`


## 開發規範
### 關於版本號
使用三節編碼格式, 採 `v{主版號}.{次版號}.{Hotfix 版號}`, e.g. v1.1.123

- 主版號
  
  面臨重大的系統結構變更, e.g. 完全單機版 -> 具備自動同步設定及中央式資料交換的連線單機版

- 次版號

  重要功能發布

- Hotfix 版號

  修正當前系統存在的問題, 不涉及對功能的變更


### 關於全局變量命名格式

採 `"全大寫 + 底線"` 格式, e.g. I_AM_GLOBAL_VARIABLE

### 關於一般欄位/局部變量命名格式

採 `"全小寫 + 底線"` 格式, e.g. i_am_local_variable

### 關於關鍵變量或配置定義

#### Exchange, Symbol 名稱規範

> 整體為二節編碼, {交易所代碼}.{商品代碼}, e.g. TWE.2330 表示台積電 (在集中交易市場, 因此是 TWE); CME.MYM202501 表示 2025/01 到期的微型道瓊期貨合約

- 交易所

    | Code  | Description |
    | :---: | :---------- |
    | TWE | 台灣證交所 |
    | TWO | 台灣櫃買上櫃 |
    | ESB | 台灣櫃買興櫃 |
    | SSE | 上海證交所 |
    | SZE | 深圳證交所 |
    | BJE | 北京證交所 |
    | TWF | 台灣期交所 |
    | JPX | 日本交易所 |
    | CBOT | 芝加哥期交所 |
    | CME | 芝商所 |
    | NYBOT | 紐約期交所 | 
    | NYMEX | 紐商所 |
    | CFE | 芝加哥期權交易所 |
    | EUREX | 歐洲期交所 |

- 商品 (搭配交易所出現)
  > 此為 SDK 直接向策略公開的常用期貨代碼, 不為各券商直接使用的代碼, 在行情/交易端應根據各券商實作 Mapping

  - 期貨季/月合約編碼方式均為 {Symbol}{到期年月}, e.g. TX202503 -> 台指期 2025/03 到期合約
  - 周合約編碼方式為 (A)BC (E)FG (I)JK (U)VW 對應 12 個月份 (英文母音做各季首月)，並由數字對應月中周次, e.g. TX2025C3 -> 台指期 2025/03 W3 到期合約
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

    
- OHLC, 即台灣常稱的 K 線

  ```python
  from pydantic import BaseModel

  import numpy


  # Timestamp 
  ohlc_dtype = numpy.dtype([("Time", "i4"),
                            ("Open", "f8"),
                            ("High", "f8"),
                            ("Low", "f8"),
                            ("Close", "f8"),
                            ("Volume", "f8")])

  # 我們假裝已經有個二維數組 ohlc_data, 即將被塞入 OHLCs object
  first_ohlc_series = OHLCs(exchange="TWF", symbol="TX202501", 
                            ohlc=numpy.array(ohlc_data, dtype=ohlc_dtype))


  class OHLCs(BaseModel):
    exchange: str
    symbol: str
    ohlc: numpy.ndarray

    
  ```


- Holiday Calendar 開/休市日曆

  開/休市時間會基於各分層設定 Overwriting, 分層為:

  - by Exchange: 基於一整個交易所進行設定, 其下所有 Symbol 通用, 常見於證券交易所或少數只有單一類型商品的期貨交易所 (e.g. 台灣期交所, 別跟我槓他有別的合約, 他並!沒!有! 其他都是死魚合約啦)
  - by Symbol: 基於單一商品進行設定, 其下各月份合約通用 (e.g. NYBOT MME 與 DX 在假日開/收盤時間不同, 因標的類型不同)

  ```python
  # Overwriting Type
  # O: Open adjust, 開市調整
  # C: Close adjust, 收盤調整
  # SS: Stop start, 休市開始 (e.g. 2025 台指期自 01/23 08:45 開始休市)
  # SE: Stop end, 休市結束 (e.g. 2025 台指期休市至 02/03 05:00)
  
  {"NYBOT.DX": {
    # 格式 [[每周開盤時間], [每周收盤時間]], 時間格式 [Weekday(0-6 -> Sun-Sat), Hour, Minute]
    "BusinessDays": [
        [0, 18, 0], [5, 17, 0]  # 每周開/收盤時間
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
    ],
    "Timezone": "US/Eastern"}
  }
  ```