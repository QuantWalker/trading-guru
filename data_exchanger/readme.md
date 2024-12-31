# 關於券商 API 實作規範

各券商 API 均由兩端組成：Market (Quote) / Trade，因此將按券商再細分為兩個專案維護

## 關於報送協議


### Heartbeat

> 用於判斷 Market / Trade API 運行狀況

發送途徑：

```QuoteAPI / TradeAPI -> Redis Key/Value```

```python
from datetime import datetime

redis_key = f"Heartbeat_Market_{instance_id}"  # 考慮多個行情實例同時啟動，負責分散處理行情
redis_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

redis_key = f"Heartbeat_Trade_{instance_id}"  # 考慮多個交易櫃台實例同時啟動，負責分散處理訂單
redis_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
```

### OHLC

> OHLC 即台灣稱的 K 棒，以下結構為 1 分鐘 OHLC (以下稱 Basic OHLC)，若策略需要其他週期 OHLC，則在 SDK 完成 OHLC 組裝處理

發送途徑：

```QuoteAPI (Producer) -> Redis Stream -> Client-SDK (Consumer) -> Strategy & TimescaleDB (Persistent)```

QuoteAPI 負責管理 Basic OHLC 的組裝及發送至 Redis Stream (僅發送完成的 Basic OHLC，正在生長中的 OHLC 由 SDK 運算及管理)，因此發送至 Stream 內的 Timestamp 必為 60 的倍數

當 QuoteAPI 接收到次一分鐘行情時，應將前一分鐘的 OHLC 閉合，並開始組裝次一分鐘 OHLC，若前一分鐘無任何成交但確信為開盤時段時，應補齊並推送該分鐘的空 OHLC (使 OHLC 保持連續以避免指標運算出現元素缺漏)

```python
# 以下為 QuoteAPI 傳入 Redis Stream 的資料範例及參數
redis_stream_key = f"OHLCs_{Exchange}.{Symbol}"
redis_stream_value = "OHLC"
message = json.dumps({
  "M": true,  # [bool] isMature，若 OHLC 是完整的為 True，若是中途才開始接收行情為 False (不成熟的 OHLC)
  "T": 1735553960,  # [long] Timestamp (seconds)，為 OHLC 的完成時間，即每分鐘的 0 秒，因此開盤時段若為 8:45 - 13:45 時，首個完整 OHLC 的應為 08:46:00，最後一個完整 OHLC 應為 13:45:00
  "O": 6014.25,  # [decimal] 開盤價
  "H": 6015.75,  # [decimal] 最高價
  "L": 6013.75,  # [decimal] 最低價
  "C": 6014.5,  # [decimal] 收盤價
  "V": 352  # [decimal] 成交量 (只有加密貨幣會有小數狀況，其他市場均應為整數)
})
message_id = str(message.get("T"))  # ID 取 Timestamp 以保證絕對遞增
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
  "A": {6014.25: 10, 6014.5: 87, 6014.75: 24, 6015: 266, 6015.25: 14}  # [OrderDict[decimal, decimal]] 賣盤報價/委託量
  "B": {6013: 148, 6013.25: 12, 6013.5: 44, 6013.75: 69, 6014: 3}  # [OrderDict[decimal, decimal]] 買盤報價/委託量
  "D": 17  # [decimal] 行情延遲 (milliseconds)，即行情品質，數值越小，品質越高
})

# "D" 欄位為 (本機時間 - (本機時間 - 券商時間) - 行情時間) 得出的 "當筆行情傳送至本機" 的延遲，若延遲過大，策略應預期此行情可能造成較大的滑價，應謹慎發送訂單，此值在大部分狀況下均應為正值，但時鐘在距離下次校時 (KGI 約 30 秒發送一次時間 Heartbeat) 發生偏差時，有可能產生負值結果。
```

### Match

> 逐筆成交資訊，另外產生基於此次成交導致此分鐘的 OHLC 最新結果

發送途徑：

```QuoteAPI (Match) -> Redis Pub/Sub```  (若希望保存 Tick 資料，可以訂閱此 Channel 並轉錄至 TimescaleDB)

```QuoteAPI (OHLC) -> Redis Key/Value```

QuoteAPI 負責接收並發送市場成交資訊，並且發送當前 OHLC 的最新狀態在 Redis Key/Value，此資訊將被用於 SDK "組裝 / 回補 OHLC"、"策略決策"、"盯市損益計算" 等用途

```python
# 以下為 QuoteAPI 更新 Redis Key/Value 的資料範例及參數
redis_key = f"OHLC_{Exchange}.{Symbol}"
redis_value = json.dumps({
  "M": true,  # [bool] isMature，若 OHLC 是完整接收時為 True，若是中途才開始接收行情為 False (不成熟的 OHLC)
  "T": 1735553960,  # [long] Timestamp (seconds)，為此 OHLC 預計完成閉合的時間，必為 60 的倍數
  "O": 6014.25,  # [decimal] 開盤價
  "H": 6015.75,  # [decimal] 最高價
  "L": 6013.75,  # [decimal] 最低價
  "C": 6014.75,  # [decimal] 收盤價
  "V": 324  # [decimal] 成交量 (只有加密貨幣會有小數狀況，其他市場均應為整數)
})

# 以下為 QuoteAPI 推播 Redis Pub/Sub 的資料範例
redis_channel = f"Match_{Exchange}.{Symbol}"
message = json.dumps({
  "T": 1735553953,  # [decimal] Timestamp (seconds)，券商不一定會給秒以下的資訊
  "ID": "123456",  # [str] 市場成交 ID
  "P": 6014.25,  # [decimal] 成交價
  "Q": 12,  # [decimal] 成交量 (只有加密貨幣會有小數狀況，其他市場均應為整數)
  "D": 21  # [decimal] 行情延遲 (milliseconds)，即行情品質，數值越小，品質越高
})

# "D" 欄位為 (本機時間 - (本機時間 - 券商時間) - 行情時間) 得出的 "當筆行情傳送至本機" 的延遲，若延遲過大，策略應預期此行情可能造成較大的滑價，應謹慎發送訂單，此值在大部分狀況下均應為正值，但時鐘在距離下次校時 (KGI 約 30 秒發送一次時間 Heartbeat) 發生偏差時，有可能產生負值結果。
```

