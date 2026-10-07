# 竹行先知｜通勤壅塞預警與容量感知分流

2026新竹縣智慧沙盒創新計畫學生組，對應[熱門提案173](https://smartsandbox.hsinchu.gov.tw/home/pageproposalcontent.html?ProposalSN=173)。初期定位：**提供交通管理者使用的通勤走廊壅塞預警與分流情境比較工具**。[完整repository](https://github.com/Kelsier64/hsinchu-smart-traffic-sandbox)保留原始檔；精簡補充ZIP省略五份全國壓縮檔。

## 完成到哪裡

- 已實作且已驗證：國道五工作日、六有向配對、8,640筆觀測的統計基準；15／30分鐘逐筆預測、全日／通勤指標；訓練均值及驗證係數獨立重算、原始保存檔hash及流程重跑。
- 已實作且已驗證主要操作：真實CSV離線回放，可選方向、日期、尺度、時點、通勤切片，查曲線與MAE／RMSE。沒有逐筆預測的日期不填模型結果。
- 已實作且已驗證函式：容量篩選與邊界測試，**假設情境，非實測成效**；未接入真實交通路網。
- 驗證有限：TDX市區29配對／23有Flows／6空為既有查詢摘要，未保存原查詢JSON；本次重新確認官方欄位規格。
- 規劃／外部依賴：市區AI預警、三策略全網比較、SUMO校準、管理者測試；民眾導航、推播及實地介入為後續延伸。

維持目前值在單一測試日最佳：15／30分全日MAE為7.75／10.75秒，通勤為15.88／22.53秒。沒有AI提升或分流改善證據；國道不能外推市區。

## 立即操作Demo

在repo根目錄執行（Python 3.10+，無套件、CDN或API金鑰）：

~~~bash
python scripts/serve_demo.py
~~~

開啟[本地歷史回放](http://127.0.0.1:8765/demo/)。若port被占用可加`--port 8766`並使用對應網址。Windows若python為商店別名，使用已安裝Python的完整路徑或py。程式只綁127.0.0.1，僅提供Demo及公開baseline檔案；勿直接file://開HTML。

[三分鐘展示腳本](submission/demo-script.md)。主要操作已由agent在瀏覽器實測；工具拒絕寫出截圖檔，沒有聲稱已保存操作截圖。

## 文件與送件交接

- [主提案來源](initial-proposal-draft.md)與[排版PDF](submission/proposal.pdf)：官方附錄七章、狀態、真實結果圖、依賴、里程碑與AI揭露。
- [官方規則查核](submission/requirements-check.md)、[實際驗證報告](submission/validation-report.md)、[AI揭露](submission/ai-disclosure.md)、[本人必辦清單](submission/human-checklist.md)。
- [容量演算法規格](submission/capacity-spec.md)、[精簡補充包](submission/supplement.zip)。
- [來源索引](OFFICIAL_SOURCES.md)、[資料研究](data-audit-and-baseline.md)、[早期研究及本次狀態更新](research-proposal-173.md)、[協作工作規格](agent-workplan.md)。

公開截止仍是2026/10/7，精確時刻與登入欄位未確認，不能宣稱目前仍受理。**隊伍／在學資訊、報名狀態、核心程式AI界線、本人查核及正式提交仍阻擋無條件送件**。PDF／補充包不是已成功提交的證明。ZIP接受格式待登入確認。

## 重算與原始流程重現

~~~bash
python -m pip install -r requirements.txt
python scripts/verify_baseline.py
python scripts/reproduce_baseline.py
python -m unittest discover -s tests -v
node --test tests/replay.test.cjs
~~~

第二個腳本核對五份repo保存M04A的hash，隔離重跑原解析／預測流程並數值比較，不覆寫基準或manifest，也不重新下載。既有下載器會拒絕來源hash變更，保留舊紀錄。新官方規則與TDX查核另存submission/evidence/public-recheck。

PDF／圖表建置需額外依賴：

~~~bash
python -m pip install -r requirements-report.txt
python scripts/build_submission.py
python scripts/package_submission.py
~~~

Windows預設嵌入微軟正黑體；其他平台設定`PROPOSAL_CJK_FONT`為可嵌入繁體中文字型TTF／TTC。修改本人資料或AI揭露後，先同步主提案，再建置PDF並重新檢視分頁。

## 資料與限制

來源：交通部高速公路局「交通資料庫」[M04A](https://tisvcloud.freeway.gov.tw/history/TDCS/M04A/)。2026/8/27、8/28、8/31訓練，9/1驗證，9/2測試。更新資料timestamp是區間起點；名義決策為起點+5分，目標結束為決策+尺度；午夜標籤仍按區間起點日期切分。

已事後修正、假設零發布延遲，沒有received_at、可信區間或事件預警驗證；全日低誤差不等於壅塞提前量。TDX VehicleCount是指定車種配對樣本，不是總流量或剩餘容量；車種3參照頁404，不直接映射M04A車種31。市區容量／方向連通／背景流量未齊，不提供真實改道或全網效益宣稱。不要提交憑證或私人行程。

程式、分析與文件包含AI生成的主要代碼。官方不建議核心主要代碼生成；必須據實揭露，本人判斷與主辦適用認定未完成。agent檢查不等於參賽者本人驗收。
