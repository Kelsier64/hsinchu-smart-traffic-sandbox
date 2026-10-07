# 實際驗證報告

日期：2026-10-07（臺灣）。由Codex agent執行，不是參賽者本人／交通管理者驗收。

## 命令與結果

本機`python`為不能執行的WindowsApps別名，改用桌面提供的Python：`C:\Users\evan4\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`；Node使用同runtime之`dependencies\node\bin\node.exe`。下列短命令代表以該完整路徑實際執行。

| 命令／操作 | 結果與範圍 |
|---|---|
| 原版`python scripts/verify_baseline.py` | 通過；原驗證未重建歷史均值／係數，午夜條件過鬆，因此加強 |
| `python -X utf8 scripts/verify_baseline.py` | 通過；8,640筆完整網格、缺值／重複／數值、切分、訓練均值、驗證係數、逐筆公式、同樣本鍵、決策與標籤、午夜、12列MAE／RMSE／n；證據`evidence/saved-audit.json` |
| `python -X utf8 scripts/reproduce_baseline.py` | 通過；5份保存壓縮檔大小／SHA256符合原manifest；隔離執行原解析及基準流程，4份CSV／audit一致，再獨立稽核；`evidence/raw-rerun.txt`。沒有重下M04A |
| `python -m unittest discover -s tests -v` | 14測試通過：9容量測試及5稽核破壞測試。刻意改壞歷史均值、標籤、評估列、午夜日期、係數時稽核會拒絕；容量涵蓋零需求／採納、滿採納、超載、未知、單位時間、非法值、禁行、路徑、瓶頸／取整。假設容量非實測 |
| `node --test tests/replay.test.cjs` | 3測試通過；前端從CSV重算全部12指標、目標實際值揭露／午夜、零預測樣本不填零誤差 |
| `python -X utf8 scripts/check_public_sources.py` | 六項HTTP200，官方頁面與TDX OpenAPI另存hash；車種參照頁404。新manifest不取代舊研究manifest |
| `python scripts/serve_demo.py --port 8766` | 本機伺服器實際啟動；桌面瀏覽器成功載入公開資料，主要控制可操作；標準啟動預設8765 |
| 實際HTTP路由查核 | Demo、JS、15分CSV皆HTTP200；`.git/config`及非展示的交接文件HTTP404 |
| `python scripts/build_submission.py`、Poppler `pdftoppm -r 90 -png` | 9頁PDF已產生，嵌入中文字型；全部頁面渲染並由agent檢視。真實曲線、12列指標來源與文字一致；這不是本人簽署／資格驗收 |
| `python scripts/package_submission.py` | ZIP完整性與容量通過；12列數字與主提案一致，本地文件引用存在；23份既有來源hash一致，允許清單文字未命中特定憑證模式；`evidence/package-check.json` |
| `python scripts/smoke_supplement.py` | 解出補充ZIP後6個回放資源HTTP200、.git/config拒絕，保存CSV獨立稽核通過；`evidence/supplement-smoke.json` |

## 瀏覽器實測

透過Codex內建瀏覽器實際操作：預設南向／15分／9/2、30分、通勤篩選、北向、下一筆、8/27觀測日、事後值揭露與23:30午夜目標；畫面顯示均與保存資料相符。無預測日顯示0筆及空白誤差；30分南向通勤84筆、MAE32.62／RMSE48.89；午夜目標23:55–次日00:00，實際162秒。已檢視完整畫面，瀏覽器警告／錯誤紀錄为空。

工具畫面截圖已顯示於執行對話；嘗試寫入repo、Downloads及工具暫存均回EPERM，**尚未保存可交付截圖檔**。不把重畫介面當成真實截圖。PDF整合真實結果圖及操作說明；本人可用展示腳本另存截圖補充。桌面未做手機或外部使用者測試。

## 失敗及處理

- 預設沙盒的Git網路DNS失敗；取得授權環境後fetch成功，遠端新增c869b21來源封存，已快轉納入工作分支，無主分支改動。
- 初次隔離重跑系統暫存寫入受限；改為repo的tmp子目錄，重跑通過，原資料未覆寫。
- 預設沙盒伺服器無法從桌面瀏覽器連線；以授權環境綁loopback的8766執行後成功。未公開對外。
- 瀏覽器截圖檔寫入受限，未冒充已有截圖；TDX車種參照頁404，車種3不映射31。
- 最終文件10個外部引用網址中9個HTTP200，SUMO以Python查核遇本機CA驗證失敗；改用瀏覽器正常開啟且讀取校準教學，未略過安全警告或停用TLS。原失敗保留`evidence/link-check.json`；原始欄位參照頁404仍未解決。
- 本機未提供pdffonts命令；改由pypdf檢查四份中文字型子集皆嵌入，再以pdfplumber檢查9頁文字無超出安全邊界，配合渲染視檢，`evidence/pdf-qa.json`。
- 進一步文字抽取發現5個空字元，來自不等式／數學減號字型映射；補上嵌入DejaVuSans符號字型並使用ASCII減號後重建，抽取無空字元且保留「≤」，再次渲染全9頁檢視。不能把初次排版檢查当作已確認所有字形。

## 驗證界線

「保存結果重算通過」與「保存原始檔流程重現通過」均完成；不是重新下載全部交通來源。無未来補值：保存觀測皆有效，沒有填補；歷史均值只由前三日、係數只由9/1生成。觀測時間、來源更新時間、實際收到時間不同；這次沒有received_at，資料已事後修正，零延遲假設不能視為真實可用性。旅行時間與車數未見數值非法，並不證明每筆量測物理正確或所有路段均完整。

TDX市區原始回應未保存，不能重驗29／23／6摘要；本次只確認新官方規格。未訓練AI交通模型，未評估壅塞事件、交通均衡、容量實測、SUMO校準、訪談／合作／分流／減碳。正式PDF、包容量與敏感資料檢查見`evidence/package-check.json`（由實際建置／檢查產生）。

新TDX OpenAPI與原研究快照SHA256相同；22頁官方簡章新舊hash亦一致。舊manifest及原CSV沒有被覆寫。正式包只採公開彙整資料，未取得私人憑證、參賽者身份文件或行程。敏感資料檢查為允許清單、特定憑證模式掃描及人工式agent閱讀範圍，不保證可辨識所有類型秘密。
