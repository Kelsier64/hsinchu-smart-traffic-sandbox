# 竹行先知｜Hsinchu Smart Traffic Sandbox

2026 新竹縣智慧沙盒創新計畫學生組研究專案，對應[熱門提案 173：AI 通勤壅塞預測與智慧分流系統](https://smartsandbox.hsinchu.gov.tw/home/pageproposalcontent.html?ProposalSN=173)。

目標：預測未來 15／30 分鐘交通，結合道路容量、資料可信度與採納率，比較改道及延後出發方案。

## 現有成果

- 官方規則與資料來源研究、依官方大綱撰寫的初選報告草稿。
- TDX 新竹縣 29 個 eTag 配對路段的靜態／即時資料實查；單次回應 23 筆有交通觀測、6 筆為空。
- 高公局五個工作日、六個國道有向配對、8,640 筆觀測的可重現離線基準。
- 15／30 分鐘逐筆預測、MAE／RMSE、日期切分與獨立重算驗證。

目前尚未完成線上產品、AI 模型、SUMO 校準或分流效果驗證。現有測試中「維持目前旅行時間」優於歷史時段及殘差校正，尚無 AI 改善證據。國道測試不能外推市區成效。

## 文件

- [參賽研究](research-proposal-173.md)
- [初選提案草稿](initial-proposal-draft.md)
- [資料實查與回測](data-audit-and-baseline.md)
- [AI agents 工作包與驗收](agent-workplan.md)
- [實驗指標](data/baseline/metrics.csv)
- [資料範圍與限制](data/baseline/audit.json)

## 重現基準

使用 Python 與 pip 安裝研究依賴，依序執行：

```bash
python -m pip install -r requirements.txt
python scripts/fetch_research_sources.py freeway_m04_catalog
python scripts/fetch_baseline_archives.py
python scripts/traffic_baseline.py
python scripts/verify_baseline.py
```

下載器只取得已在官方目錄確認的五個公開彙整檔案，已存在的壓縮檔不重複下載。全國原始下載檔與官方網頁快取不納入 Git；來源 URL 與 SHA256 保存在 `data/research/baseline-source-manifest.json`。選取觀測與逐筆預測保存在 `data/baseline/`。

資料來源：交通部高速公路局「交通資料庫」[M04A](https://tisvcloud.freeway.gov.tw/history/TDCS/M04A/)。時間語意、事後修正、發布延遲假設與單日測試限制詳見研究文件。

TDX 正式自動收集所需帳號及憑證尚未設定；不得提交 API 金鑰或個人行程資料。研究程式與文件由 AI 協助建立，提交競賽前須由參賽者閱讀、查核並據實揭露。

## 下一階段

先建立真實歷史資料回放 Demo：路段地圖、時間軸、基準與實際值比較、資料品質提示；再依取得的市區歷史資料發展預測及容量感知分流。
