# CWA 農業氣象預報（Streamlit）

以中央氣象署開放資料 F-A0010-001（檔案型資料，fileapi）打造的互動儀表板，含台灣地圖標示各區天氣、最高/最低溫，並提供 7 天溫度趨勢比較。

## 需求
- Python 3.9+ 建議
- pip 套件：`streamlit` `requests` `pandas` `pydeck` `plotly`

快速安裝：
```bash
pip install -r requirements.txt
```

## 環境變數
- `CWA_API_KEY`：中央氣象署授權碼。若未設定，程式會使用示例金鑰，請務必改成自己的金鑰以避免流量/權限問題。

## 執行
```bash
streamlit run main.py
```
預設會在瀏覽器開啟本機網址，若未自動開啟可手動複製終端機上的 URL。

線上 Demo：
- https://qcv7vzlmtcuvabs2so3kty.streamlit.app/

## 功能概覽
- 台灣地圖（pydeck）：依溫度藍→紅色階顯示點位，滑鼠提示白底黑字顯示圖示、地名、最高/最低溫與天氣描述。
- KPI 摘要：顯示地點數、資料日期範圍、地圖顯示日期。
- 今日表格：列出選定日期的天氣圖示、最高/最低溫、降雨機率。
- 7 天折線圖：可多選地點，同圖比較最高/最低溫。
- 資料更新與來源註記：頁面顯示資料更新時間與 CWA 資源代碼。

## 常見問題
- **404 或抓取失敗**：F-A0010-001 是檔案型資料，必須使用 `https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/` 並帶 `downloadType=WEB&format=JSON`，本程式已採用此路徑。
- **地圖缺點**：若某地點未顯示，請在 `TAIWAN_COORDS` 補上該 `locationName` 的座標。
- **SSL 憑證錯誤**：若環境缺少可用憑證，程式會自動嘗試 `verify=False` 並在畫面顯示警告。請先更新系統/`certifi` 憑證，或設定 `REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE` 指向系統 CA；臨時測試可設 `CWA_VERIFY_SSL=0`，但建議盡快恢復驗證。

## 開發提示
- 若需重抓資料，可點擊側邊欄「重新抓取資料」或在終端機執行 `streamlit cache clear` 再重啟。
- 自訂配色或字型可修改 `main.py` 開頭的 CSS 區塊。
