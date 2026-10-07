# 官方簡章與研究來源索引

保存日期：2026-10-07（臺灣）。本repo保存已取得之官方文件及資料快照；原始內容與權利歸各發布單位，引用時仍須標註來源。資料快照不保證與後續公告相同；本次新查核另存[公開查核manifest](submission/evidence/public-recheck/manifest.json)，不覆寫舊來源。正式送件狀態仍待本人確認。

## 競賽簡章與官方頁面

| 本地檔案 | 官方來源／用途 |
|---|---|
| [簡章 PDF：20260806版本](official-rules-20260806.pdf) | [官方下載](https://smartsandbox.hsinchu.gov.tw/Document/2026%E6%96%B0%E7%AB%B9%E7%B8%A3%E6%99%BA%E6%85%A7%E6%B2%99%E7%9B%92%E5%89%B5%E6%96%B0%E8%A8%88%E7%95%AB%E7%AB%B6%E8%B3%BD%E7%B0%A1%E7%AB%A0.pdf?v=20260806)；資格、評分、交件、AI揭露及報告大綱 |
| [簡章擷取文字](official-rules.txt) | 由上述PDF擷取，方便搜尋；排版及表格以PDF為準 |
| [題目173頁面快照](data/research/official-proposal-173.html) | [官方題目](https://smartsandbox.hsinchu.gov.tw/home/pageproposalcontent.html?ProposalSN=173) |
| [競賽說明快照](data/research/official-competition.html) | [規則、期程與簡章入口](https://smartsandbox.hsinchu.gov.tw/home/pagesmartsand.html) |
| [參賽流程快照](data/research/official-how-to-play.html) | [官方流程](https://smartsandbox.hsinchu.gov.tw/home/pagehowtoplay.html) |
| [消息列表快照](data/research/official-news.html) | [官方最新消息](https://smartsandbox.hsinchu.gov.tw/home/pagenews.html) |
| [熱門題列表快照](data/research/official-wishpool.html) | [許願池](https://smartsandbox.hsinchu.gov.tw/home/pagewishpage.html) |

HTML為原始回應快照，不包含所有網站圖片、樣式、JavaScript及其呼叫的動態內容；需看完整服務時開啟官方連結。

注意：先前查閱的官方網頁銀／銅獎金與PDF有差異，研究中已保留此待確認事項，不能自行選一個數值當成已解決。公開截止日期為10/7，精確截止時刻尚未由登入後台確認。

## 交通資料、規格與原始彙整檔

| 檔案／目錄 | 內容與來源 |
|---|---|
| [高公局資料庫首頁快照](freeway-index.html) | [交通部高速公路局「交通資料庫」](https://tisvcloud.freeway.gov.tw/) |
| [TDCS使用手冊PDF](data/research/tdcs-manual.pdf)／[文字](data/research/tdcs-manual.txt) | [官方v41b手冊](https://tisvcloud.freeway.gov.tw/documents/TDCS%E4%BD%BF%E7%94%A8%E6%89%8B%E5%86%8Av41b.pdf)；M04A欄位、秒數單位、即時與修正資料的時間差異 |
| [TDX路況API規格](data/research/tdx-traffic-oas.json) | [官方OpenAPI規格](https://tdx.transportdata.tw/webapi/File/Swagger/V3/7f07d940-91a4-495d-9465-1c9df89d709c)；規格列出端點不代表每個縣市皆有完整資料 |
| [國道VD靜態XML](data/research/vd-static.xml) | [官方來源](https://tisvcloud.freeway.gov.tw/history/motc20/VD.xml)；全國設備靜態資料 |
| [國道eTag靜態XML](data/research/etag-static.xml) | [官方來源](https://tisvcloud.freeway.gov.tw/history/motc20/ETag.xml) |
| [新竹周邊VD篩選JSON](data/research/hsinchu-freeway-vd.json) | 本研究依經緯度矩形篩選VD XML的衍生資料；包含匝道、縣市與鄰近邊界，不能當作新竹縣有效設備總數 |
| [歷史目錄快照](data/research/history-catalog.html) | [官方歷史資料說明](https://tisvcloud.freeway.gov.tw/history-list.php) |
| [M04A目錄快照](data/research/m04a-catalog.html) | [旅行時間檔案目錄](https://tisvcloud.freeway.gov.tw/history/TDCS/M04A/) |
| [M05A目錄快照](data/research/m05a-catalog.html)／[單日目錄](data/research/m05a-day-catalog.html) | [速度檔案目錄](https://tisvcloud.freeway.gov.tw/history/TDCS/M05A/)；本次基準採用M04A，未以此目錄作訓練資料 |
| `data/research/M04A_20260827.tar.gz`等五個壓縮檔 | 8/27、8/28、8/31、9/1、9/2全國五分鐘彙整資料；六個國道路段的選取結果另存於`data/baseline/` |

五個M04A壓縮檔約20.5MB，均為彙整資料，沒有下載M06A逐旅次原始資料。資料引用請保留「交通部高速公路局『交通資料庫』」。

## 研究、提案與證據

- [完整參賽研究](research-proposal-173.md)
- [初選報告草稿](initial-proposal-draft.md)
- [實際資料查詢、回測方法與限制](data-audit-and-baseline.md)
- [AI agents分工](agent-workplan.md)
- [逐筆觀測及預測結果](data/baseline/)
- [研究與重現腳本](scripts/)

TDX市區回應目前保存在研究文件中的查詢摘要，沒有把完整瀏覽器回應匯出成原始JSON；API規格檔不等於該次觀測。這個限制不能因保存了其他官方來源而忽略。

## 追溯與更新

[完整來源清單與SHA256](data/research/official-source-manifest.json)列出官方下載檔及衍生檔，避免混淆研究結論與官方原文。[五日下載紀錄](data/research/baseline-source-manifest.json)保存原始檔URL與hash；[其他來源下載紀錄](data/research/source-fetch-log.json)包含成功與失敗的查詢。

早期下載記錄曾被腳本覆寫，因此部分檔案沒有保留精確下載時間；目前清單不推測缺失時間。紀錄中的`/history/motc20/VDLive/`曾回應404，沒有對應檔案，不能視為已取得VD歷史資料；官方歷史目錄另列VD子目錄，尚未下載驗證。

重新產生檔案清單：`python scripts/build_source_manifest.py`。此命令只讀取本地來源檔案並更新清單，不會重新下載或宣稱取得最新版。
