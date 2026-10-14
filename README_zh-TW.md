
[English](README_en.md) | [简体中文](README.md) | [繁體中文](README_zh-TW.md)

# 1. Python  分佈式函數調度平臺 Funboost 簡介

[![pZf68L6.png](https://s41.ax1x.com/2026/01/30/pZf68L6.png)](https://imgchr.com/i/pZf68L6)

**Funboost** 是一個 Python 分佈式函數調度平臺。以下是您的核心學習資源導航：

| 資源類型 | 鏈接地址 | 說明 |
| :--- | :--- | :--- |
| ⚡ **快速預覽** | [👉 點擊查看演示](https://ydf0509.github.io/funboost_git_pages/funboost_promo.html) | 直觀感受框架運行效果 |
| 📖 **完全教程** | [👉 ReadTheDocs](https://funboost.readthedocs.io/zh-cn/latest/index.html) | 包含原理、API 與進階用法 |
| 🤖 **AI 助教** | [👉 AI 學習指南](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) | **[必讀]** 利用 AI 掌握框架的最佳捷徑 |
| 📄 **超級 AI 上下文文檔** | [👉 funboost_all_docs_and_codes.md](https://github.com/ydf0509/funboost/blob/master/funboost_all_docs_and_codes.md) | 約 900K 上下文，包含 Rules、Skills、完整教程、源碼和使用 Demo，直接投餵給 AI 即可讓它幫你寫代碼 |


## 1.0 funboost 框架說明介紹

`funboost`是一個 萬能 強大 簡單  自由 的 `python` 全功能分佈式調度框架,是一個 Python 分佈式函數調度平臺,它的作用是給用戶任意項目的任意函數賦能

**Funboost 的核心價值主張：把複雜留給框架，把簡單留給用戶。**

<iframe src="https://ydf0509.github.io/funboost_git_pages/index2.html" width="100%" height="2400" style="border:none;"></iframe>


<h4>📹 觀看 funboost 視頻</h4>
<video controls width="800" 
      src="https://ydf0509.github.io/funboost_git_pages/%E8%A7%86%E9%A2%91-Funboost_%E8%A7%86%E9%A2%91.mp4">
   您的瀏覽器不支持視頻播放。
</video>

<h4>🎧 收聽 funboost 音頻</h4>
<audio controls 
      src="https://ydf0509.github.io/funboost_git_pages/%E9%9F%B3%E9%A2%91-funboost_%E9%9F%B3%E9%A2%91.mp4">
   您的瀏覽器不支持音頻播放。
</audio>

### 1.0.1 funboost 示意圖


#### 1.0.1.1 funboost 運行流程圖

funboost 採用經典的 **生產者 → Broker → 消費者** 架構模型，並支持可選的 RPC 模式（消費者 → 生產者）。

雖然 funboost 的功能豐富度遠超 scrapy 等專業框架，但其架構設計卻保持了極致的簡潔性，核心流程一目瞭然。

![funboost 運行流程圖](img_95.png)

#### 1.0.1.2 funboost 功能思維導圖

funboost使用極其簡單，只有一行@boost，但是用戶能想得到的功能全都有。良好的軟件設計架構，以致funboost框架可以擴展無限可能。

從funboost 思維導圖來看，funboost支持 40+ 種消息隊列支持、30+ 種任務控制功能、所有python併發模式、roc、微批消費、cdc事件驅動、 funboost管理可視化、分佈式定時任務、faas 熱加載、workflow任務編排、boost_spider爬蟲、promethus指標監控、opentelemetry全鏈路任務追蹤等， 適用範圍頂python編程半邊天。

思維導圖圖片分辨率大，建議下載保存，用本地圖片軟件查看。
<!-- ![funboost 功能思維導圖](img_94.png) -->
![funboost 功能思維導圖](mermaid-diagram0311e.png)



### 1.0.2 快速瞭解和上手funboost，直接看[1.3例子](#13-框架使用例子)


### 1.0.3 funboost 框架安裝方式  

```shell
pip install funboost --upgrade  

或 pip install funboost[all]  #一次性安装所有小众三方中间件  
```  


### 1.0.4 funboost 功能作用

- **萬能分佈式調度**：`funboost` 通過一行 @boost 裝飾器，將普通函數瞬間升級為具備 分佈式執行、FaaS 微服務化、CDC 事件驅動 能力的超級計算單元，連接一切，調度萬物。
- **全能支持**：自動支持 **40+種** 消息隊列 + **30+種** 任務控制功能 + `python`中**所有**的併發執行方式。
- **FaaS 能力**：通過 `funboost.faas` 的功能，可以一鍵快速實現 **FaaS (Function as a Service)**，讓函數秒變自動發現的微服務。

- **重功能，輕使用**：
   `funboost` 的功能是**全面性重量級**，用戶能想得到的功能 99% 全都有；但使用方式卻是**極致輕量級**，只有 `@boost` 一行代碼需要寫。

- **顛覆性設計**：
   `funboost` 的神奇之處在於它同時擁有“**輕量級使用方式**”和“**重量級功能集**”，完全顛覆了“功能強大=使用複雜”的傳統思維。它是對傳統 Python 框架設計的一次巧妙超越。
   
   只需要一行 `@boost` 代碼即可分佈式執行 `python` 一切任意函數，99% 用過 `funboost` 的 `pythoner` 核心感受是：**方便、高速、強大、自由**。  



#### 1.0.4.1 Funboost 的適用場景

`funboost` 是 **Python 函數的萬能加速器**。它包羅萬象，一統編程思維，將經典的 **生產者 + 消息中間件 + 消費者** 模式封裝到了極致。

無論新老項目，Funboost 都能無縫融入，為您提供以下核心能力：

*   🌐 **需要分佈式？**
    沒問題！Funboost 支持 **40+種** 消息隊列中間件。只要是叫得上名字的 MQ（甚至包括數據庫、文件系統），它都能支持。

*   ⚡ **需要 FaaS (Function as a Service)？**
    **這是亮點！** 藉助 `funboost.faas`，您可以一鍵將普通函數轉化為 HTTP 微服務接口。函數自動發現，發佈消息、獲取結果、管理任務，瞬間完成 Serverless 般的體驗。

*   🚀 **需要併發？**
    滿足你！Python 所有的併發模式（**線程、協程、多進程**）任你選擇，甚至支持它們**疊加使用**，榨乾 CPU 性能。

*   🛡️ **需要可靠性？**
    穩如泰山！**消費確認 (ACK)**、自動重試、死信隊列 (DLQ)、斷點續爬... 即使服務器宕機，任務也絕不丟失。

*   🎛️ **需要控制力？**
    如臂使指！**精準 QPS 控頻**、分佈式限流、定時任務、延時任務、超時熔斷、任務過濾... 給您三十多種控制武器。

*   📊 **需要監控？**
    一目瞭然！開箱即用的 **funweb (Funboost Web Manager)**，讓您對任務狀態、隊列積壓、消費者實例等信息瞭如指掌。

*   🦅 **需要自由？**
    零侵入！它不綁架您的代碼，不強管您的項目結構。**隨時能用，隨時能走**，還您最純粹的 Python 編程體驗。


#### 1.0.4.2 🤔 靈魂發問：Funboost 到底是什麼？

**Funboost 的功能已經極其豐富，甚至可以用“功能過剩”或“全能怪獸”來形容。**

> **Funboost 早已超越了“任務隊列框架”的傳統定義，它已進化為新一代的「分佈式函數調度平臺 (Universal Function Computing Platform)」。**
>
> 如果說 Celery 是異步任務的“工具”，那麼 Funboost 則是函數計算的“基礎設施”。它不僅完美覆蓋了 Celery 的核心能力，更打破了技術棧的邊界，以**“函數”**為原子核心，貪婪地吞噬並融合了 **FaaS、RPC、微服務架構、網絡爬蟲、實時數據同步 (CDC/ETL) 、IOT（MQTT）、分佈式定時任務、部署、運維；並完整支持 事件驅動 (EDA) 與 全鏈路可觀測性（OpenTelemetry）**。
>
> 在 Funboost 的世界裡，不再是對標 Celery，而是重新定義 Python 函數的生產力邊界。

> **答**：很難用一句話定義它。Funboost 是一個**萬能框架**，幾乎覆蓋了 Python 所有的編程業務場景。它的答案是發散的，擁有無限可能。

👉 **[點擊查看發散性答案 (文檔 6.0b 章節)](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#b-funboost)**

#### 1.0.4.3 💖 核心關切：值得我投入時間學習嗎？

> **答**：**絕對值得**。選擇一個用途狹窄、性能平庸、寫法受限的框架，確實是在浪費生命。Funboost 則完全不同。

👉 **[查看詳細評估報告 (文檔 6.0 章節)](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html#funboost)**


#### 1.0.4.4 Funboost 與 Celery 的理念區別

> **核心比喻**：
> `funboost` 與 `celery` 的關係，如同 **iPhone** 與 **諾基亞塞班**。
> 它們的核心功能雖都是通訊（任務調度），但不能因為功能重疊就判定為重複造輪子。正如 iPhone 重新定義了手機，**Funboost 正在重新定義分佈式任務調度，讓“框架奴役”成為歷史。**

**1. 共同點**
兩者本質上都是基於分佈式消息隊列的異步任務調度框架，遵循經典的編程思想：
*   `生產者 (Producer)` -> `中間件 (Broker)` -> `消費者 (Consumer)`

**2. 核心區別**

| 維度 | **Celery (重型框架)** | **Funboost (函數增強器)** |
| :--- | :--- | :--- |
| **設計理念** | **框架奴役**：代碼需圍繞 Celery 的架構和 App 實例組織。 | **自由賦能**：非侵入式設計，為任意函數插上分佈式的翅膀。 |
| **一等公民** | `Celery App` 實例 (Task 是二等公民) | **用戶函數** (無需關注 App 實例) |
| **核心語法** | 需定義 App，使用 `@app.task` | 直接使用 **`@boost`** 裝飾器 |
| **易用性** | 需規劃特定的項目結構，上手門檻較高。 | 極簡，任意位置的新舊函數加上裝飾器即可用。 |
| **性能表現** | 傳統性能基準。 | **斷層式領先**：發佈性能是 Celery 的 **22倍**，消費性能是 **46倍**。 |
| **功能廣度** | 支持主流中間件。 | 支持 **40+** 種中間件，擁有更多精細的任務控制功能。 |
| **AI 輔助編程** | 官方文檔需人工親自閱讀，學習成本高。 | **超級 AI 上下文文檔**：`funboost_all_docs_and_codes.md`<br>（約 900K 上下文），可直接投餵給 AI，讓 AI 幫你寫代碼、解答問題，無需吃苦看文檔。 |


#### 1.0.4.5 Funboost 支持的併發模式

`funboost` 全面覆蓋 Python 生態下的併發執行方式，並支持靈活的組合疊加：

*   **基礎併發模式**：支持 `threading` (多線程)、`asyncio` (異步IO)、`gevent` (協程)、`eventlet` (協程) 以及 `單線程` 模式。
*   **疊加增強模式**：支持 **多進程 (Multi-Processing)** 與上述任一細粒度併發模式（如多線程或協程）進行疊加，最大限度利用多核 CPU 資源。

#### 1.0.4.6 Funboost 支持的消息隊列中間件 (Broker)

得益於強大的架構設計，在 `funboost` 中 **“萬物皆可為 Broker”**。不僅涵蓋了傳統 MQ，更拓展了數據庫、網絡協議及第三方框架。

*   **傳統消息隊列**：RabbitMQ, Kafka, NSQ, RocketMQ, MQTT, NATS, Pulsar 等。
*   **數據庫作為 Broker**：
    *   **NoSQL**: Redis (支持 List, Pub/Sub, Stream 等多種模式), MongoDB.
    *   **SQL**: MySQL, PostgreSQL, Oracle, SQL Server, SQLite (通過 SQLAlchemy/Peewee 支持).
*   **網絡協議直連**：TCP, UDP, HTTP, gRPC (無需部署 MQ 服務即可實現隊列通信)。
*   **文件系統**：本地文件/文件夾, SQLite (適合單機或簡單場景).
*   **事件驅動 (CDC)**：支持 **MySQL CDC** (基於 Binlog 變更捕獲)，使 Funboost 具備了事件驅動能力，設計理念遠超傳統任務隊列。
*   **第三方框架集成**：可直接將 Celery, Dramatiq, Huey, RQ, Nameko 等框架作為底層 Broker，利用 Funboost 的統一接口調度它們的核心。





#### 1.0.4.7 **funboost 學習難嗎?**   


**答案是：極易上手。Funboost 是“反框架”的框架。**

*   🎯 **核心極簡**
    整個框架只需要掌握 **`@boost`** 這一個裝飾器及其入參（`BoosterParams`）。所有的用法幾乎都遵循 **1.3 章節** 示例的模式，一通百通。

*   🛡️ **零代碼侵入**
    *   **拒絕“框架奴役”**：不像 `Celery`、`Django` 或 `Scrapy` 那樣強迫你按照特定的目錄結構組織代碼（一旦不用了，代碼往往需要大改）。
    *   **即插即用**：Funboost 對你的項目文件結構 **0 要求**，你可以隨時將其引入任何新老項目中。

*   🔄 **進退自如（雙模運行）**
    即使引入了 Funboost，也不需要擔心代碼被綁定。加上 `@boost` 裝飾器後，你的函數依然保持純潔：
    *   調用 `fun(x, y)`：**直接運行函數**（同步執行，不經過隊列，即使加了裝飾器也和沒加裝飾器一樣）。
    *   調用 `fun.push(x, y)`：**發送到消息隊列**（分佈式異步執行）。

*   🤖 **面向 AI 編程的超級ai上下文文檔**
    Funboost 提供了 **`funboost_all_docs_and_codes.md`**（約 900K 上下文），包含完整教程、源碼和示例。你可以直接將其投餵給 AI（如 DeepSeek、Gemini 等百萬上下文模型），讓 AI 幫你快速生成 Funboost 代碼、解答問題或定製擴展，實現極致的 AI 輔助編程體驗。

👉 *關於"Funboost 學習和使用難嗎？"的詳細深度回答，請參閱文檔 **`6.0.c`** 章節。*


#### 1.0.4.8 📊 可視化監控與管理
Funboost 內置了強大的 **funweb (Funboost Web Manager)** 管理系統。
*   **全方位掌控**：支持對任務消費情況進行全面的查看、監控和管理。
*   **開箱即用**：無需額外部署複雜的監控組件，即可掌握隊列積壓、消費者狀態等核心指標。

#### 1.0.4.9 🚀 性能表現：斷層式領先
Funboost 的性能與 Celery 相比，有著**數量級**的優勢（基於控制變量法測試）：
*   **發佈性能**：是 Celery 的 **22倍**。
*   **消費性能**：是 Celery 的 **46倍**。
> *注：詳細的控制變量法對比測試報告，請參閱文檔 **2.6 章節**。*

#### 1.0.4.10 ⭐ 用戶口碑與評價
**95% 的用戶**在初步使用後都表示“相見恨晚”。核心評價如下：
*   **極致自由**：Funboost 對用戶代碼的編程思維**零侵入**。
*   **拒絕改造**：不像其他框架要求用戶圍繞框架邏輯重構代碼，Funboost 尊重用戶的原生代碼結構。
*   **核心體驗**：簡單、強大、豐富。






## 1.1 📚 核心資源與文檔導航

### 1.1.1 📝 項目文檔入口

> **🚀 快速上手指南**
>
> *   **文檔說明**：文檔篇幅較長，主要包含原理講解與框架對比（`How` & `Why`）。
> *   **學習捷徑**：**您只需要重點學習 [1.3 章節] 的這 1 個例子即可！** 其他例子僅是修改 `@boost` 裝飾器中 `BoosterParams` 的入參配置。
> *   **核心要點**：`funboost` 極其易用，僅需掌握一行 `@boost` 代碼。
> *   **🤖 AI 輔助**：強烈推薦閱讀 **[第 14 章]**，學習如何利用 AI 大模型快速掌握 `funboost` 的用法。

**🔗 在線文檔地址**：[ReadTheDocs - Funboost Latest](https://funboost.readthedocs.io/zh-cn/latest/index.html)
**超級ai上下文文檔**：[funboost_all_docs_and_codes.md](https://github.com/ydf0509/funboost/blob/master/funboost_all_docs_and_codes.md)


#### 📖 文檔章節速覽

| 🔰 基礎入門 & 核心概念 | 🚀 進階功能 & 場景實戰 | 🤖 AI 輔助 & 問題排查 |
| :--- | :--- | :--- |
| [1. funboost 框架簡介](https://funboost.readthedocs.io/zh-cn/latest/articles/c1.html) | [4b. 代碼示例 (**高級進階**)](https://funboost.readthedocs.io/zh-cn/latest/articles/c4b.html) | [**14. AI 輔助學習指南 (必讀)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c14.html) |
| [2. funboost 對比 Celery](https://funboost.readthedocs.io/zh-cn/latest/articles/c2.html) | [8. 爬蟲實戰：自由編程 vs 框架奴役](https://funboost.readthedocs.io/zh-cn/latest/articles/c8.html) | [6. 常見問題 Q&A](https://funboost.readthedocs.io/zh-cn/latest/articles/c6.html) |
| [3. 框架詳細介紹](https://funboost.readthedocs.io/zh-cn/latest/articles/c3.html) | [9. 輕鬆遠程服務器部署](https://funboost.readthedocs.io/zh-cn/latest/articles/c9.html) | [10. 常見報錯與問題反饋](https://funboost.readthedocs.io/zh-cn/latest/articles/c10.html) |
| [4. **各種代碼示例 (核心)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c4.html) | [11. 集成第三方框架 (Celery/Kombu等)](https://funboost.readthedocs.io/zh-cn/latest/articles/c11.html) | [7. 更新記錄](https://funboost.readthedocs.io/zh-cn/latest/articles/c7.html) |
| [5. 運行時截圖展示](https://funboost.readthedocs.io/zh-cn/latest/articles/c5.html) | [12. 命令行控制檯支持](https://funboost.readthedocs.io/zh-cn/latest/articles/c12.html) | [20. Gemini AI 生成的框架中心思想](https://funboost.readthedocs.io/zh-cn/latest/articles/c20.html) |
| | [13. funweb 可視化管理](https://funboost.readthedocs.io/zh-cn/latest/articles/c13.html) | |
| | [⚡ **15. FaaS Serverless 微服務 (戰略級核心)**](https://funboost.readthedocs.io/zh-cn/latest/articles/c15.html) | |

---

### 1.1.2 📦 源碼與依賴

*   **GitHub 項目主頁**：[ydf0509/funboost](https://github.com/ydf0509/funboost)
*   **nb_log 日誌文檔**：[NB-Log Documentation](https://nb-log-doc.readthedocs.io/zh_CN/latest/articles/c9.html#id2)
   
---

## 1.2 框架功能介紹  

有了 `funboost`，開發者將獲得“上帝視角”的調度能力：
*   🚫 **告別繁瑣**：無需親自手寫進程、線程、協程的底層併發代碼。
*   🔌 **萬能連接**：無需親自編寫操作 `Redis`、`RabbitMQ`、`Kafka`、`Socket` 等中間件的連接代碼。
*   🧰 **全能控制**：直接擁有 30+ 種企業級任務控制功能。

**funboost示圖：**  
![funboost示圖](https://s21.ax1x.com/2024/04/29/pkFFghj.png)


**也就是這種非常普通的流程圖,一樣的意思**  
![funboost示圖](https://s21.ax1x.com/2024/04/29/pkFFcNQ.png)

### 1.2.1 🆚 對比：Funboost 取代傳統線程池

以下兩種方式均實現 **10併發** 運行函數 `f`。Funboost 更加簡潔且具備擴展性。

#### ❌ 方式 A：手動開啟線程池 (傳統)
```python
import time
from concurrent.futures import ThreadPoolExecutor

def f(x):
    time.sleep(3)
    print(x)

pool = ThreadPoolExecutor(10)

if __name__ == '__main__':
    for i in range(100):
        pool.submit(f, i)
```

#### ✅ 方式 B：Funboost 模式 (推薦)
```python
import time
from funboost import BoosterParams, BrokerEnum

# 仅需一行装饰器，即可获得 10 线程并发 + 消息队列能力
@BoosterParams(queue_name="test_insteda_thread_queue", 
               broker_kind=BrokerEnum.MEMORY_QUEUE, 
               concurrent_num=10, 
               is_auto_start_consuming_message=True)
def f(x):
    time.sleep(3)
    print(x)

if __name__ == '__main__':
    for i in range(100):
        f.push(i)
```

### 1.2.2 🚀 任務控制功能矩陣

Funboost 將分佈式系統的複雜性封裝於內核，向下屏蔽基礎設施差異，向上提供標準化的調度原語。以下是框架核心能力的 **7 維全景視圖**：

#### 🌌 維度一：連接與架構 (Connectivity & Architecture)

| 能力模塊 | 技術特性說明 |
| :--- | :--- |
| **Broker 適配** | **40+ 協議支持**：RabbitMQ, Kafka, RocketMQ, Pulsar, NATS, Redis (List/Stream/PubSub), SQL/NoSQL, 文件系統, TCP/UDP/HTTP。 |
| **FaaS 微服務** | **自動路由**：通過 `funboost.faas`，消費函數自動註冊為 FastAPI/Flask/Django 接口；支持 **服務發現** 與 **熱更新**。 |
| **CDC 事件驅動** | **Binlog 監聽**：支持 `MYSQL_CDC`，實現數據庫變更實時觸發函數執行，輕量級替代 Canal/Flink 組件。 |
| **框架託管** | **無縫兼容**：支持接管 Celery, Dramatiq, RQ, Huey 等框架作為底層驅動，統一上層 API。 |
| **異構通信** | **多協議支持**：支持 gRPC 雙向通信與 MQTT 物聯網協議集成。 |
| **超級裝飾器** | **funboost當做超級裝飾器使用**：即使你不用消息隊列，也建議使用funboost，因為@boost控制函數功能極其豐富 |

#### ⚡ 維度二：併發與吞吐 (Concurrency & Throughput)

*   **混合併發模型**：原生支持 `Threading`、`Gevent`、`Eventlet`、`Asyncio` (原生事件循環)、`Single_thread` 五種模式。
*   **多進程疊加**：支持 `mp_consume(n)`，在上述併發模式之上疊加 **多進程**，突破 GIL 限制，充分利用多核 CPU。
*   **微批處理 (Micro-Batch)**：提供 `MicroBatchConsumerMixin`，支持自動緩衝聚合單條消息進行批量處理（如批量 DB 寫入），顯著提升 I/O 吞吐。
*   **零拷貝模式**：內存隊列支持 `Ultra-Fast` 模式，跳過序列化開銷，實現進程內微秒級通信。

#### 🛡️ 維度三：可靠性保障 (Reliability)

*   **心跳級 ACK**：基於消費者心跳檢測的 ACK 機制。可識別進程僵死或崩潰，**秒級**回收並重發未確認任務，避免長耗時任務被誤判。
*   **異常重試**：支持指數退避策略，支持針對特定異常類型的重試配置。
*   **死信隊列 (DLQ)**：重試耗盡或捕獲特定異常後，自動將消息移交死信隊列，保障現場數據不丟失。
*   **全量持久化**：支持將函數入參、執行結果、耗時、異常堆棧自動持久化至 MongoDB/MySQL，實現數據可回溯。
*   **多維監控告警**：內置**五種開箱即用的告警方式**（內置告警 Mixin、熔斷器鉤子、Prometheus 指標、Mongo 輪詢、ELK 日誌），可按連續失敗次數或滑動窗口錯誤率配置告警規則，支持釘釘、企業微信、飛書、Webhook 等多種通道；任務恢復後自動發送恢復通知，形成故障感知與解決的完整閉環。（在文檔 **6.30 funboost 如何實配置觸發失敗告警和恢復告警** 一節中有詳細說明）


#### 🕹️ 維度四：流量治理 (Traffic Governance)

*   **精準控頻 (QPS)**：原生支持從極低頻（0.00001次/秒）到高頻（50000次/秒）的 **QPS 速率限制**，以**勻速間隔**的方式執行任務。
*   **週期額度 (Quota)**：支持在指定週期（如1分鐘）內限制任務執行的**總次數**，任務可**隨到隨執行**（非勻速）。例如：設置"每分鐘最多執行100次"，100次額度用完後將等待下一週期。此功能用法詳見 **4b.12 章節**。
*   **分佈式限流**：基於funboost的Redis 心跳信息協調，實現跨服務器、跨容器的 **全局流量控制**。
*   **分組消費**：支持 `consume_group`，按業務組別啟動消費者，實現大單體應用的資源隔離。
*   **手動熔斷管理**：支持運行時動態下發指令，實時 **暫停/恢復** 指定隊列的消費。
*   **自動熔斷管理**：使用CircuitBreakerConsumerMixin擴展，支持自動熔斷、半開、恢復，支持阻塞模式和降級模式。
*   **批處理流控**：提供 `wait_for_possible_has_finish_all_tasks`，支持腳本級的**任務清空等待**。

#### 🎼 維度五：調度與編排 (Scheduling & Orchestration)

*   **Workflow 編排**：內置聲明式編排原語，支持 **Chain (串行)**、**Group (並行)**、**Chord (回調)** 模式。
*   **分佈式定時**：集成 `APScheduler`，支持 Crontab/Interval/Date 觸發器，利用分佈式鎖防止多實例重複執行。
*   **延時任務**：原生支持 `countdown` (相對時間) 和 `eta` (絕對時間) 的延遲調度。
*   **任務去重**：基於函數入參指紋進行去重（支持 TTL 有效期），屏蔽 URL 隨機參數干擾。

#### 🔭 維度六：可觀測性 (Observability)

*   **鏈路追蹤**：原生集成 **OpenTelemetry**，支持接入 Jaeger/SkyWalking，自動注入 Context 實現跨組件全鏈路追蹤。
*   **指標監控**：內置 **Prometheus** Exporter，支持 Pull 和 PushGateway 模式，通過 Grafana 展示實時指標。
*   **Web 控制檯**：自帶可視化管理界面，支持查看積壓量、QPS 曲線、消費者元數據
*   **遠程運維**：支持 `RemoteTaskKiller` 終止特定執行中的任務；支持 `fabric_deploy` 實現代碼熱部署。
                funweb (funboost_web_manager) 支持腳本更新和部署/進程存活監控/日誌查看/便捷的文件日誌檢索

#### 🧬 維度七：開發體驗 (Developer Experience)

*   **FCT 上下文**：提供 `from funboost import fct` 全局對象，在函數調用鏈任意位置獲取 TaskID、重試次數等元數據。
*   **全語法支持**：完整支持 **類方法 (classmethod)**、**實例方法 (instance method)**、**異步函數 (async def)** 作為消費主體。
*   **生命週期 Hook**：提供 `consumer_override_cls` 接口，支持重寫消息清洗、結果回調等核心邏輯，兼容 **非標準格式消息**，**支持重寫任何任意父類方法**。
*   **對象傳輸**：支持 Pickle 序列化選項，允許直接傳遞自定義 Python 對象作為任務參數。
*   **超級裝飾器**： 即使用戶不需要分佈式和消息隊列，也可以使用 `@boost` 裝飾器配合 **MEMORY_QUEUE** 模式，一個@boost裝飾器就能實現併發控制、QPS 限流、自動重試、任務去重等 10+ 種功能，抵得上 10 個常規裝飾器疊加使用。





## 1.3 🚀 快速上手：你的第一個 Funboost 程序

> **⚠️ 環境準備 (重要)**
>
> 在運行代碼前，請確保您瞭解 **`PYTHONPATH`** 的概念。
> Windows cmd 或 Linux 運行時，建議將 `PYTHONPATH` 設置為項目根目錄，以便框架自動生成或讀取配置。
> 👉 [點擊學習 PYTHONPATH](https://github.com/ydf0509/pythonpathdemo)

### 1.3.1 ✨ Hello World：最簡單的任務調度

這個例子演示瞭如何將一個普通的求和函數變成分佈式任務。

**代碼邏輯說明：**
1.  **定義任務**：使用 `@boost` 裝飾器，指定隊列名 `task_queue_name1` 和 QPS `5`。
2.  **發佈任務**：調用 `task_fun.push(x, y)` 發送消息。
3.  **消費任務**：調用 `task_fun.consume()` 啟動後臺線程自動處理。

```python
import time
from funboost import boost, BrokerEnum, BoosterParams

# 核心配置：使用本地 SQLite 作为消息队列，QPS 限制为 5
@boost(BoosterParams(
    queue_name="task_queue_name1", 
    qps=5, 
    broker_kind=BrokerEnum.SQLITE_QUEUE
))
def task_fun(x, y):
    print(f'{x} + {y} = {x + y}')
    time.sleep(3)  # 模拟耗时，框架会自动并发绕过阻塞

if __name__ == "__main__":
    # 1. 生产者：发布 100 个任务
    for i in range(100):
        task_fun.push(i, y=i * 2)
    
    # 2. 消费者：启动循环调度
    task_fun.consume()
```

> **💡 Tips**
> 如果在 Linux/Mac 上使用 `SQLITE_QUEUE` 報錯 `read-only`，請在 `funboost_config.py` 中修改 `SQLLITE_QUEUES_PATH` 為有權限的目錄（詳見文檔 10.3）。

**運行效果截圖：**

**發佈任務截圖：**
![發佈截圖](https://s21.ax1x.com/2024/04/29/pkFkP4H.png) 

**消費任務截圖：**
![消費截圖](https://s21.ax1x.com/2024/04/29/pkFkCUe.png)



### 1.3.2 🔥 進階實戰：RPC、定時任務與絲滑連招

這是一個集大成的例子，展示了 Funboost 的核心能力：
*   ✅ **參數複用**：繼承 `BoosterParams` 減少重複代碼。
*   ✅ **RPC 模式**：發佈端同步獲取消費結果。
*   ✅ **絲滑啟動**：非阻塞連續啟動多個消費者。
*   ✅ **定時任務**：基於 `APScheduler` 的強大定時能力。

```python
import time
from funboost import boost, BrokerEnum, BoosterParams, ctrl_c_recv, ConcurrentModeEnum, ApsJobAdder

# 1. 定义公共配置基类，减少重复代码
class MyBoosterParams(BoosterParams):
    broker_kind: str = BrokerEnum.REDIS_ACK_ABLE
    max_retry_times: int = 3
    concurrent_mode: str = ConcurrentModeEnum.THREADING 

# 2. 消费函数 step1：演示 RPC 模式
@boost(MyBoosterParams(
    queue_name='s1_queue', 
    qps=1,   
    is_using_rpc_mode=True  # 开启 RPC，支持获取结果
))
def step1(a: int, b: int):
    print(f'step1: a={a}, b={b}')
    time.sleep(0.7)
    # 函数内部可以继续发布任务给 step2
    for j in range(10):
        step2.push(c=a+b+j, d=a*b+j, e=a-b+j)
    return a + b

# 3. 消费函数 step2：演示参数覆盖
@boost(MyBoosterParams(
    queue_name='s2_queue', 
    qps=3, 
    max_retry_times=5  # 覆盖基类默认值
)) 
def step2(c: int, d: int, e: int=666):
    time.sleep(3)
    print(f'step2: c={c}, d={d}, e={e}')
    return c * d * e

if __name__ == '__main__':
    # --- 启动消费 ---
    step1.consume()  # 非阻塞启动
    step2.consume()
    step2.multi_process_consume(3) # 叠加 3 个进程并发

    # --- RPC 调用演示 ---
    async_result = step1.push(100, b=200)
    print('RPC 结果：', async_result.result)  # 阻塞等待结果

    # --- 批量发布演示 ---
    for i in range(100):
        step1.push(i, i*2)
        # publish 方法支持更多高级参数（如 task_id）
        step1.publish({'a':i, 'b':i*2}, task_id=f'task_{i}')

    # --- 定时任务演示 (APScheduler) ---
    # 方式1：指定日期执行
    ApsJobAdder(step2, job_store_kind='redis', is_auto_start=True).add_push_job(
        trigger='date', run_date='2025-06-30 16:25:40', args=(7, 8, 9), id='job1'
    )
    # 方式2：间隔执行
    ApsJobAdder(step2, job_store_kind='redis').add_push_job(
        trigger='interval', seconds=30, args=(4, 6, 10), id='job2'
    )

    # 阻塞主线程，保持程序运行
    ctrl_c_recv()
```

> **🧠 設計哲學**
> Funboost 提倡 **“反框架”** 思維：你才是主角，框架只是插件。
> `task_fun(1, 2)` 是直接運行函數，`task_fun.push(1, 2)` 才是發佈到隊列。
> 隨時可以拿掉 `@boost`，代碼依然是純粹的 Python 函數。

---

### 1.3.3 ✂️ 極簡寫法：省略 `@boost`

如果你追求極致簡潔，也可以直接使用 `@BoosterParams` 作為裝飾器，效果等同於 `@boost(BoosterParams(...))`。

```python
# 极简写法
@BoosterParams(queue_name="task_queue_simple",qps=5)
def task_fun(a, b):
    return a + b
```

### 1.3.4 ❌ 過時寫法： 直接在 @boost傳各種配置入參，不推薦
這種直接在 `@boost`傳參，而不使用 `BoosterParams`來傳各種配置，是過氣寫法不推薦，因為不能代碼補全了。   
```python
# ⚠️ 反例：过时写法，不推荐！
@boost(queue_name="task_queue_simple",qps=5)
def task_fun(a, b):
    return a + b
```


## 🖥️ funweb (Funboost Web Manager) 界面預覽

可視化管理後臺提供了強大的監控與運維能力，以下是核心功能截圖：



函數消費結果：可查看和搜索函數實時消費狀態和結果  
[![函數結果表](https://s41.ax1x.com/2025/12/19/pZ1L5h4.png)](https://imgchr.com/i/pZ1L5h4)

隊列操作：查看和操作隊列，包括清空、暫停消費、恢復消費、調整QPS和併發  
[![隊列操作1](https://s41.ax1x.com/2025/12/17/pZlrYPH.png)](https://imgchr.com/i/pZlrYPH)
[![隊列操作2](https://s41.ax1x.com/2025/12/17/pZlrUxI.png)](https://imgchr.com/i/pZlrUxI)

隊列操作：查看消費曲線圖，查看各種消費指標（歷史運行次數、失敗次數、近10秒完成/失敗、平均耗時、剩餘消息數量等）  
[![隊列消費曲線](https://s41.ax1x.com/2025/12/19/pZ104HS.png)](https://imgchr.com/i/pZ104HS) 

RPC調用：在網頁上對30種消息隊列發佈消息並獲取函數執行結果；可根據task_id獲取結果  
[![rpc調用成功-綠色](https://s41.ax1x.com/2025/12/19/pZ10RjP.png)](https://imgchr.com/i/pZ10RjP)

定時任務管理：列表頁  
[![定時任務列表](https://s41.ax1x.com/2025/12/17/pZlrNRA.png)](https://imgchr.com/i/pZlrNRA)



## 1.4 💡 為什麼 Python 極其需要分佈式函數計算？

Python 語言的特性決定了它比 Java/Go 等語言更依賴分佈式調度框架。主要原因有兩點：

### 1️⃣ 痛點一：GIL 鎖的限制 (多核利用率低)
> 🛑 **現狀**：由於 GIL (全局解釋器鎖) 的存在，普通的 Python 腳本無法利用多核 CPU。在 16 核機器上，CPU 利用率最高只能達到 **6.25% (1/16)**。
> 😓 **難點**：手動編寫 `multiprocessing` 多進程代碼非常麻煩，涉及複雜的進程間通信 (IPC)、任務分配和狀態共享。

✅ **Funboost 的解法**：
*   **天生解耦**：利用中間件（如 Redis/RabbitMQ）解耦任務,無法手寫怎麼給多進程分配任務和進程間通信。
*   **無感多進程**：單進程腳本與多進程腳本寫法完全一致，**無需**手寫 `multiprocessing`，自動榨乾多核性能。

### 2️⃣ 痛點二：原生性能瓶頸 (動態語言特性)
> 🐌 **現狀**：作為動態語言，Python 的單線程執行速度通常慢於靜態語言。
> 🚀 **需求**：為了彌補單機速度，必須通過**橫向擴展**來換取時間。

✅ **Funboost 的解法**：
*   **無縫擴展**：代碼無需任何修改，即可適應多種運行環境：
    *   🔄 **多解釋器**：同一臺機器啟動多個 Python 進程。
    *   🐳 **容器化**：部署在多個 Docker 容器中。
    *   ☁️ **跨物理機**：部署在多臺物理服務器上。
*   **統一驅動**：Funboost 作為調度核心，讓 Python 跑在集群之上，獲得媲更高的系統吞吐量。


## 1.5 🎓 最佳學習路徑

Funboost 的設計哲學是 **“極簡主義”**。您無需閱讀長篇大論，只需通過實踐掌握核心：

1.  **🧪 實驗式學習**：
    *   以 **1.3 章節** 的求和代碼為藍本。
    *   修改 `@boost` 裝飾器中的參數（如 `qps`、`concurrent_num`）。
    *   在函數中添加 `time.sleep()` 模擬耗時。
    *   **觀察**：觀察控制檯輸出，體會分佈式、併發和控頻的實際效果。

2.  **✨ 一行代碼原則**：
    *   這是最簡單的框架：核心只有一行 `@boost` 代碼。
    *   如果您能掌握這個裝飾器，就掌握了整個框架。這比學習那些需要繼承多個類、配置多個文件的傳統框架要簡單得多。

> **🤖 AI 助教**
> 強烈推薦參考 **[文檔第 14 章]**，學習如何利用 AI 大模型快速精通 `funboost` 的各種高級用法。

---

## 1.6 🥋 funboost 練就吸星大法神功，一招吸走 Celery 畢生內力

**Funboost 的極簡招式 + Celery 的深厚內力 = 獨步武林**

> “江湖中人多迷信 Celery 的名門光環，雖 Funboost 身法快過其數十倍，且有演武場（2.6章節）實測為證，奈何部分豪傑固步自封，不願親自試劍。
> Funboost 遂施展 **‘吸星大法’**，將 Celery 納為己用（作為 Broker）。**既入我門，便由我控**，以此化解眾生執念。”

Celery 稱霸 Python 異步江湖十數載，內力雖深厚，但其招式繁複、門規森嚴（配置繁瑣），令無數豪傑望而卻步。 
今 Funboost 施展 **“吸星大法”**，只需一招 `BrokerEnum.CELERY`，頃刻間將 Celery 化為 **座下護法**。自此，Celery 竟成 Funboost 之一大 **子集**，聽憑號令！ 

### ⚔️ 降維打擊：化繁為簡的絕世武功
通過 Funboost 駕馭 Celery，猶如令狐沖習得獨孤九劍，破盡天下繁瑣招式，直擊要害：

| 🆚 招式對決 | 🛑 原生 Celery (舊派宗門的桎梏) | 🟢 Funboost 御劍術 (新派宗師的灑脫) |
| :--- | :--- | :--- |
| **啟動法門**<br>(部署) | **唸誦咒語**：需死記硬背 `worker/beat` 等冗長命令行，稍有錯漏便走火入魔。 | **意念合一**：代碼即啟動，無需記憶任何咒語，`python xx.py` 一劍破萬法。 |
| **門派規矩**<br>(結構) | **清規戒律**：強行規定目錄結構，錯置文件即被逐出師門，極其僵化。 | **無招勝有招**：飛花摘葉皆可傷人，任意目錄、任意文件皆可為戰場，毫無束縛。 |
| **心法運轉**<br>(門檻) | **經脈逆行**：需手動修煉 `includes` 和 `task_routes`，極易氣血翻湧（配置報錯）。 | **渾然天成**：自動打通任督二脈，框架自動發現並註冊任務，行雲流水。 |
| **洞察天地**<br>(體驗) | **盲人摸象**：`@app.task` 入參如霧裡看花，IDE 無法感知，極易行差踏錯。 | **天眼通**：`BoosterParams` 開啟全知視角，代碼補全如神助，所見即所得。 |

> **📜 藏經閣 (代碼示例)**
> 欲練此功，請翻閱 **[11.1 章節]**。
> 您只需施展 Funboost 的極簡劍法，底層那擁有萬鈞之力的 Celery 引擎便會自動為您移山填海，雖有雷霆之威，卻無反噬之虞。


 需要說明的是，funboost性能是已經遠超celery，吸納celery作為broker，兼容celery作為funboost的broker，是為了打消有的人對funboost的調度核心的穩定性的疑慮。   
 > 你可以看文檔2.6章節**funboost vs celery控制變量法性能對比**，以及2.9章節，**funboost到底為什麼性能比celery高几十倍？太離譜了,太假了是嗎？**


[查看 funboost 分佈式函數調度平臺 完整教程](https://funboost.readthedocs.io/)  

![](https://visitor-badge.glitch.me/badge?page_id=distributed_framework)  

<div> </div>  

[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  
[//]: #  

