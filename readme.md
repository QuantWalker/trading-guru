# QuantWalker 程式交易平台
這是一個由眾多交易者與程式開發者共同維護的社群項目，所有源碼均以 GPL 授權方式公開。平台的初衷是提供一個低門檻 (不是無門檻，若不具備基本程式開發能力的話，這個平台就不適合你了) 的程式交易系統，供大家進行策略運行。同時，也歡迎有志於共同打造更便利系統的專家加入這個社群。

> 免責聲明: 所有使用者須對其交易行為負全責，任何交易指令所產生的結果均與本平台無關。在投入正式交易環境前，您即被視為已充分了解本平台的功能與技術實現，本平台對於可能存在的 Bug 或其他潛在問題概不負責。


## 使用之前的準備
您應向開戶券商申請 API 使用權限並安裝相應的交易憑證在終端機才能開始接收行情，申請詳情請洽您的券商營業員。

### 平台可使用券商
> 券商選擇是基於 API 穩定性為首要考量
- 元大
- 凱基
- 群益
- 富邦


## 運行環境最低需求
佈署方式將因您選擇的券商而有不同，您也可以將所有組件都運行在同一個裝置，以下將個別列出主要組件的運行環境最低需求。
- 策略端: 
  - Linux/Windows 10 (or Above)
  - Python 3.10 (or Above)

- 通信/快取中間件: 
  - Redis 7

- 本地存儲:
  - PostgreSQL (with TimescaleDB)

- 行情/交易端 (依據券商決定運行環境): 
  - Windows: 元大 / 凱基 / 群益 
  - Linux: 富邦

### 推薦佈署模式
- All-in-one (以帳戶開立在 元大 / 凱基 / 群益的情境為例)
  - 1 x Windows Server 2022 (2 vCPU, 4G RAM) 在其安裝 Redis 7, PostgreSQL 等組件並啟動行情/交易端進程後即可啟動策略端進程開始運行

- Cloud IaaS/Paas (以 AWS 及帳戶開立在 元大 / 凱基 / 群益為例)
  - 1 x EC2 (Windows Server 2022 t3.small): 負責運行行情/交易端 
  - 1 x ElastiCache (Redis 7.4): 負責中間通信
  - 1 x ECS: 負責運行策略端 (可內含 PostgreSQL 或選擇其他 DB 方案)


## 平台功能
- 即時交易 SDK:
  > 可提供策略連接以讀取行情並發送交易指令，具備標準化後的行情報文格式及交易指令，可經此 SDK 連線至指定券商主機
  - 支援開發環境: Python 3.10 or Above
  - 負責連線管理，具備斷線重連等機制
  - 具備已定義的行情資料結構及交易指令函數
  - 具備交易國內證券 / 期貨 / 海外期貨市場，尚未計劃支持加密貨幣市場 (但可擴展)
  - 訂單生命週期管理及倉位統計功能，降低策略端開發工作量
  - 具備常見技術指標運算函式，策略可按需調用
  - 具備 Paper Trading 模式，可用於策略 Forward Testing
  
- 通用報文規範
  > 行情及交易指令標準化，使 SDK 可通用與任意券商交換資訊

- Forward Testing 可視化模組
  > 用於檢視進出場點位執行狀況及各項績效統計指標

- 主要券商 API 行情/交易終端
  > 使用 C#, C++, Java, Python 等語言直接對券商, 加密貨幣交易所提供之 API 進行開發，並轉化為通用報文以便 SDK 調用 


## 文檔歷史
- 2024-12-20 ver 0.1.0
  > 第一代功能閹割版文件出爐，在這個版本受制於台灣金融法規問題，使我們捨棄了很多選項，在這個版本的目標是實現大家可以自行佈署並使用的 MVP 產品，因此在一些配置文檔需要用戶定期下載更新方式處理，不會建置一個 Server 來提供此類服務。
  - 運行環境及推薦佈署模式
  - 即時交易 SDK 功能定義
  - 通用行情及交易通訊規範

- xxxx-xx-xx ver 0.2.0 (預計)
  > 在此次文檔預計釋出包含交易端實作功能以及訂單生命週期管理等規格，目標實現自 "上次斷線 - 本次啟動連線" 時同步仍處於 open 的訂單資訊
  - 交易端重連時的實作規範
  - Forward Testing 可視化模組設計
