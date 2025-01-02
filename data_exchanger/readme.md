# 關於券商 API 實作規範

各券商 API 均由兩端組成：Market (Quote) / Trade，因此將按券商再細分為兩個專案維護，並在報送過程中 (無論上 / 下行報送方向)，保持以下兩個標準：
- 交易量一律採用最小計量單位，即：股、個、口(手)
- 價格一律採用十進位制

> 舉例來說，台股一張是 1,000 股，因此當券商報量單位為 "張" 時，應轉換為股數 (張 * 1,000)，這樣系統就能兼容美股、台灣零股、期貨、加密貨幣的交易場景

在 OpenSource 版本，您可以啟動多個行情實例以分散行情訂閱，因為券商通常會規範每個連線能訂閱的行情數量限制，但您仍需注意券商相關 API 使用規範 (例如：連線數上限、每個連線訂閱上限、每秒鐘的請求數上限)，避免導致因濫用 API 而被券商停權。

每一套交易櫃台實例只會對應連接一個實體帳號。此外，在 OpenSource 版本，一個策略 SDK 進程僅能向一套交易櫃台發送交易指令，即您無法在此版本中使用如 "期現貨套利" 一類需要同時交易證券及期貨市場的策略。

在首次啟動策略前，您必須使用介面對策略設定注入資金 (寫入 SQLite 及 InfluxDB)，當設定資金低於實際帳戶資金時，TradeAPI 將阻止您的新倉訂單 (僅接受平倉)，這是 `因為系統始終無法感知實體帳戶出入金、來自系統外的訂單指令又或是此實體帳戶同時存在其他子帳戶狀況，因此系統將會根據每日結算資料在啟動時，主動運算策略可動用資金`。

另外，當您使用同一實體帳號 `進行手動 & 程序化交易時`，TradeAPI 將忽略未經 SDK 下發的訂單 / 成交回報 (例如，您在同一帳戶使用券商 App 下單)。

## 關於報送協議
以下為使用到的報送協議整理表，詳細內文格式請見各項描述

| Medium | Channel/Key Name | Description |
| :----: | :---: | :---------- |
|                 |  **System Monitor**             |                       |
| Redis Key/Value | Heartbeat_Market_{instance_id} | 行情 API 進程運行狀況 |
| Redis Key/Value | Heartbeat_Trade_{instance_id} | 交易 API 進程運行狀況 |
|                 |   **Market Data**             |                              |
| Redis Stream    | OHLCs_{exchange}.{symbol}     | 傳送已閉合的 OHLC (1 分 OHLC) |
| Redis Pub/Sub   | Depth_{exchange}.{symbol}     | 交易盤口資訊 |
| Redis Pub/Sub   | Match_{exchange}.{symbol}     | 逐筆交易資訊 |
| Redis Key/Value | OHLC_{exchange}.{symbol}      | 目前最新 OHLC (1 分 OHLC) |
|                 |   **Order Data**              |                              |
| Redis Stream    | Order_{counter_alias}         | 訂單委託 / 撤單指令           |
| Redis Stream    | OrderAck_{strategy_name}      | 委託回報                     |
| Redis Stream    | Trade_{strategy_name}         | 成交回報                     |
| Redis Stream    | Account_{strategy_name}       | 帳戶資訊                     |

### Heartbeat

> 用於判斷 Market / Trade API 運行狀況

發送途徑：

```QuoteAPI / TradeAPI -> Redis Key/Value```

```python
from datetime import datetime

# 考慮同時啟動不同交易所或是多個 QuoteAPI 實例狀況，應設計 instance_id 做為啟動 QuoteAPI / TradeAPI 的參數，用於識別實例

time_format = "%Y-%m-%dT%H:%M:%S.%f%z"  # 2025-01-02T08:45:00.000000+0800

redis_key = f"Heartbeat_Market_{instance_id}"  # 考慮多個行情實例同時啟動，負責分散處理行情
redis_value = datetime.now().strftime(time_format)

redis_key = f"Heartbeat_Trade_{instance_id}"  # 考慮多個交易櫃台實例同時啟動，負責處理不同交易所或券商的訂單
redis_value = datetime.now().strftime(time_format)
```

### OHLC

> OHLC 即台灣稱的 K 棒，以下結構為 1 分鐘 OHLC (以下稱 Basic OHLC)，若策略需要其他週期 OHLC，則在 SDK 完成 OHLC 組裝處理

發送途徑：

```QuoteAPI (Producer) -> Redis Stream -> Client-SDK (Consumer) -> Strategy```

```QuoteAPI -> InfluxDB```

QuoteAPI 負責管理 Basic OHLC 的組裝及發送至 Redis Stream (僅發送完成的 Basic OHLC，正在生長中的 OHLC 由 SDK 運算及管理)，因此發送至 Stream 內的 Timestamp 必為 60 的倍數

當 QuoteAPI 接收到次一分鐘行情時，應將前一分鐘的 OHLC 閉合，並開始組裝次一分鐘 OHLC，若前一分鐘無任何成交但確信為開盤時段時，應補齊並推送該分鐘的空 OHLC (使 OHLC 保持連續以避免指標運算出現元素缺漏)

```python
# 以下為 QuoteAPI 傳入 Redis Stream 的資料範例及參數
redis_stream_key = f"OHLCs_{Exchange}.{Symbol}"
redis_stream_value = "OHLC"
message = json.dumps({
  "M": True,  # [bool] isMature，若 OHLC 是完整的為 True，若是中途才開始接收行情為 False (不成熟的 OHLC)
  "T": 1735553960,  # [long] Timestamp (seconds)，為 OHLC 的完成時間，即每分鐘的 0 秒，因此開盤時段若為 8:45 - 13:45 時，首個完整 OHLC 的應為 08:46:00，最後一個完整 OHLC 應為 13:45:00
  "O": 6014.25,  # [decimal] 開盤價
  "H": 6015.75,  # [decimal] 最高價
  "L": 6013.75,  # [decimal] 最低價
  "C": 6014.5,  # [decimal] 收盤價
  "V": 352  # [decimal] 成交量 (股數，台股一張為 1,000 股，只有加密貨幣會有小數狀況，其他市場均應為整數)
})
message_id = str(1735553960)  # ID 取 Timestamp (T 欄位) 以保證絕對遞增
max_length = 1440  # Stream 最多保有 1440 個 OHLC 避免無限制擴張 stream key 影響 redis 性能
approximate_max_length = True  # 使用約略長度修剪模式，獲得較好的 redis 性能表現
```

### Depth

> 盤口資訊

```QuoteAPI (Depth) -> Redis Pub/Sub```

```python
# 以下為 QuoteAPI 推播 Redis Pub/Sub 的資料範例
redis_channel = f"Depth_{Exchange}.{Symbol}"
message = json.dumps({
  "T": 1735553953,  # [decimal] Timestamp (seconds)，券商不一定會給秒以下的資訊
  "A": {6014.25: 10, 6014.5: 87, 6014.75: 24, 6015: 266, 6015.25: 14}  # [OrderedDict[decimal, decimal]] 賣盤報價/委託量, Top 20 檔 (避免加密貨幣訂單簿太長)
  "B": {6013: 148, 6013.25: 12, 6013.5: 44, 6013.75: 69, 6014: 3}  # [OrderedDict[decimal, decimal]] 買盤報價/委託量, Top 20 檔 (避免加密貨幣訂單簿太長)
  "D": 17  # [int] 行情延遲 (milliseconds)，即行情品質，數值越小，品質越高
})

# "D" 欄位為 (本機時間 - (本機時間 - 券商時間) - 行情時間) 得出的 "當筆行情傳送至本機" 的延遲，若延遲過大，策略應預期此行情可能造成較大的滑價，應謹慎發送訂單，此值在大部分狀況下均應為正值，但時鐘在距離下次校時 (KGI 約 30 秒發送一次時間 Heartbeat) 發生偏差時，有可能產生負值結果。
```

### Match

> 逐筆成交資訊，另外產生基於此次成交導致此分鐘的 OHLC 最新結果

發送途徑：

```QuoteAPI (Match) -> Redis Pub/Sub```  (若希望保存 Tick 資料，可以啟用一個獨立進程訂閱此 Channel 並轉錄至 InfluxDB)

```QuoteAPI (OHLC) -> Redis Key/Value```

QuoteAPI 負責接收並發送市場成交資訊，並且發送當前 OHLC 的最新狀態在 Redis Key/Value，此資訊將被用於 SDK "組裝 / 回補 OHLC"、"策略決策"、"盯市損益計算" 等用途

```python
# 以下為 QuoteAPI 更新 Redis Key/Value 的資料範例及參數
redis_key = f"OHLC_{Exchange}.{Symbol}"
redis_value = json.dumps({
  "M": True,  # [bool] isMature，若 OHLC 是完整接收時為 True，若是中途才開始接收行情為 False (不成熟的 OHLC)
  "T": 1735553960,  # [long] Timestamp (seconds)，為此 OHLC 預計完成閉合的時間，必為 60 的倍數
  "O": 6014.25,  # [decimal] 開盤價
  "H": 6015.75,  # [decimal] 最高價
  "L": 6013.75,  # [decimal] 最低價
  "C": 6014.75,  # [decimal] 收盤價
  "V": 324  # [decimal] 成交量 (股數，台股一張為 1,000 股，只有加密貨幣會有小數狀況，其他市場均應為整數)
})

# 以下為 QuoteAPI 推播 Redis Pub/Sub 的資料範例
redis_channel = f"Match_{Exchange}.{Symbol}"
message = json.dumps({
  "T": 1735553953,  # [decimal] Timestamp (seconds)，券商不一定會給秒以下的資訊
  "ID": "123456",  # [str] 市場成交 ID
  "P": 6014.25,  # [decimal] 成交價
  "Q": 12,  # [decimal] 成交量 (股數，台股一張為 1,000 股，只有加密貨幣會有小數狀況，其他市場均應為整數)
  "D": 21  # [int] 行情延遲 (milliseconds)，即行情品質，數值越小，品質越高
})

# "D" 欄位為 (本機時間 - (本機時間 - 券商時間) - 行情時間) 得出的 "當筆行情傳送至本機" 的延遲，若延遲過大，策略應預期此行情可能造成較大的滑價，應謹慎發送訂單，此值在大部分狀況下均應為正值，但時鐘在距離下次校時 (KGI 約 30 秒發送一次時間 Heartbeat) 發生偏差時，有可能產生負值結果。
```

### Order

> 訂單指令，由策略經 SDK 向下發送至 Redis Stream，並 upsert 至 SQLite 及建立委託紀錄 / 日誌至 InfluxDB

發送途徑：

```SDK (Producer) -> Redis Stream -> Trade API (Consumer)```

```SDK -> SQLite (SQLite 時間格式將改為 2025-01-02T08:45:00.000000+0800)```

所有策略訂單發送均預期為限價，不接受市價發送訂單，若策略開發所需，可改用較劣勢價格 (買更貴，賣便宜) 發出以實現範圍限價效果

```python
redis_stream_key = f"Order_{CounterAlias}"
order = json.dumps({
    "CT": "",  # [decimal] Timestamp (seconds), 此處為指令發起時間
    "PID": "",  # [str] 指令 Private ID，為 SDK 產生以利後續響應時辨識，不可重複
    "OT": "",  # [str] Literal["NO", "CO"]，指令類型：新單 (New Order)、撤單 (Cancel Order)
    "SN": "",  # [str] 策略機 Alias，用於多策略時分發訂單響應流資訊
    "E": "",  # [str] 標準化交易所代碼
    "S": "",  # [str] 標準化標的代碼
    "D": "",  # [str] Literal["B", "S"], 買賣方向
    "PE": "",  # [str] Literal["AP", "NP", "CP", "DT"]，訂單指定開平倉：自動 (Auto Position)、新倉 (New Position)、平倉 (Close Position)、日內交易 (Day Trade) (標的或交易所只能支援部分指令，此資訊將宣告在產品設定檔中)
    "TIF": "",  # [str] Literal["ROD", "FOK", "IOC", "GTC"]，訂單時效：當日有效 (Rest of Day)、全部成交否則取消 (Fill or Kill)、立即成交其餘取消 (Immediate or Canel)、長期有效直至取消 (Good till Cancel) (標的或交易所一般只能支援部分指令，此資訊將宣告在產品設定檔中)
    "P": "",  # [decimal] 十進制委託價格 (由 API 層根據券商要求轉換為對應報價進制格式)
    "Q": "",  # [decimal] 委託量 (均以最小單位發出，例如：股、口(手)、個，由 API 根據券商要求轉換為對應單位)
    "EP": "",  # [Optional(dict)] 擴展屬性，用於保存其他用於改單 / 撤單的附屬資訊 (新單時為空值)
})

# EP 欄位資訊範例，以凱基為例 (這些資訊與策略無關，但是撤單時會需要發送，各券商欄位不同，欄位命名依 TradeAPI 方便解析及發送為主)：
extended_property = {
    "BrokerId": "",
    "Account": "",
    "FCM": "",
    "FFUT_ACCOUNT": "",
    "CNT": "",
    "Ordno": "",
    "TradeDate": "",
    "WEBID": ""
}
```

### OrderAck

> 訂單響應，由 TradeAPI 向上發送 Redis Stream，並 upsert 至 SQLite 及更新委託紀錄並建立日誌至 InfluxDB

發送途徑：

```Trade API (Producer) -> Redis Stream -> SDK (Consumer)```

```Trade API -> SQLite (SQLite 時間格式將改為 2025-01-02T08:45:00.000000+0800)```

```python
redis_stream_key = f"OrderAck_{StrategyName}"

# 結構與 Order 部分相同，新增 TradeAPI 及券商側產生的資訊
order_ack = json.dumps({
    "CT": "",  # [decimal] Timestamp (seconds), 此處為訂單建立時間 (因為只有仍在場上的訂單會有券商 Ack，其他應視為系統外部產生的訂單或是錯誤單號，應在 TradeAPI 層面忽略並寫入 Warning Level Log)
    "PID": "",
    "RID": "",  # [str] 由 TradeAPI 產生的 Request ID，各家產生的機制略有不同，由此映射由異步途徑返回的訂單紀錄
    "SN": "",
    "E": "",
    "S": "",
    "D": "",
    "PE": "",
    "TIF": "",
    "P": "",
    "Pc": "",  # [str] 轉換後實際委託報出價格，根據券商對此商品的報價格式紀錄
    "Q": "",
    "MQ": "",  # [decimal] Matched Quantity, 已成交數量
    "MV": "",  # [decimal] Matched Value, 已成交金額 (用於反推平均成交價，MV += 成交單量 * 實際成交價)
    "MP": "",  # [decimal] Matched Price, (十進位制) 平均成交價格
    "OS": "",  # [str] Literal["Pending", "Sent", "Partial", "Filled", "Killed", "Rejected"]，訂單最新狀態，若訂單部分成交後取消成功時，狀態仍然為 Killed (因為最終是停在撤單成功狀態)；活躍可被取消的訂單狀態為：Pending, Sent, Partial, 其他均為已成/撤訂單
    "MT": "",  # [decimal | None] Timestamp (seconds)， 訂單撤銷時間
    "UT": "",  # [decimal] Timestamp (seconds)， 訂單狀態更新時間
    "EP": "",  # [dict] 擴展屬性，用於保存其他用於改單 / 撤單的附屬資訊
})
```

### Trade

> 訂單逐筆成交回報，由 TradeAPI 向上發送 Redis Stream，並 upsert 至 SQLite 及更新委託紀錄並建立日誌至 InfluxDB

發送途徑：

```Trade API (Producer) -> Redis Stream -> SDK (Consumer)```

```Trade API -> SQLite (SQLite 時間格式將改為 2025-01-02T08:45:00.000000+0800)```

```python
redis_stream_key = f"Trade_{StrategyName}"

trade = json.dumps({
    "CT": "",  # [decimal] Timestamp (seconds), 此處為成交時間
    "PID": "",
    "SN": "",
    "E": "",
    "S": "",
    "D": "",
    "XP": "",  # [decimal] Executed Price, (十進位制) 成交價
    "XPc": "",  # [str] 原券商報價格式之成交價
    "XQ": "",  # [decimal] Executed Quantity, 成交量
    "OS": ""  # [str] Literal["Partial", "Filled"] 訂單受此成交影響後的最新狀態，僅會有列舉的兩種可能
})
```

### Account

