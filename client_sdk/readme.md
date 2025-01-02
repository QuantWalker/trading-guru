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

