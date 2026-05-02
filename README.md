# 🛡️ Google Workspace 資料外洩防護（DLP）監控系統

---

⚠️ 注意：
本專案使用 Google OAuth 進行驗證，
請自行建立 credentials.json 並放入專案目錄，請參考以下步驟。

---

## 🔐 建立 `credentials.json`（Google OAuth 設定）

本專案使用 Google Drive API 進行資料存取，需先建立 OAuth 憑證。

---

### 📌 Step 1：建立 Google Cloud 專案

1. 前往 Google Cloud Console
   https://console.cloud.google.com/

2. 點擊「選擇專案」 →「新增專案」

3. 輸入專案名稱（例如：`workspace-dlp`）

---

### 📌 Step 2：啟用 API

進入專案後：

1. 左側選單 →「API 和服務」→「程式庫」

2. 搜尋並啟用以下 API：

* Google Drive API
* Google Drive Activity API（選用）
* Admin SDK API（選用）

---

### 📌 Step 3：設定 OAuth 同意畫面

1. 左側選單 →「API 和服務」→「OAuth 同意畫面」

2. 使用者類型選擇：

   * 學校 / 公司帳號 → **Internal**
   * 個人帳號 → **External**

3. 填寫：

   * 應用程式名稱（例如：DLP System）
   * 使用者支援電子郵件

4. 儲存並完成

---

### 📌 Step 4：建立 OAuth 用戶端 ID

1. 左側選單 →「API 和服務」→「憑證」

2. 點擊「建立憑證」→「OAuth 用戶端 ID」

3. 選擇應用程式類型：

```text
桌面應用程式（Desktop App）
```

4. 建立後下載 JSON 檔案

---

### 📌 Step 5：放入專案

將下載的檔案重新命名為：

```text
credentials.json
```

並放入專案根目錄：

```text
drive_dlp_project/
├── app.py
├── main.py
├── credentials.json  ← 放這裡
```

---

### ⚠️ 安全注意事項

* ❌ 不要將 `credentials.json` 上傳到 GitHub
* ❌ 不要公開 OAuth 憑證
* 建議加入 `.gitignore`：

```text
credentials.json
token.json
.env
```

---

### ▶️ 第一次執行

執行程式時：

```bash
streamlit run app.py
```

系統會自動開啟瀏覽器，請登入 Google 帳號並授權。

授權後會自動產生：

```text
token.json
```

用於後續存取。

---


## 📌 專案簡介

為確保安全性，credentials.json 並未包含於 repository 中。

本專案實作一套基於 **Google Workspace（Google Drive）** 的資料外洩防護（Data Loss Prevention, DLP）監控系統。

系統可自動分析檔案分享行為、偵測外部存取、計算風險分數，並提供可解釋（Explainable AI, xAI）的資安分析結果。

---

## 🎯 專案目標

* 偵測 Google Drive 中的 **外部分享行為**
* 辨識可能包含 **敏感資訊的文件**
* 建立 **風險評分機制（Risk Scoring）**
* 提供 **可解釋的資安分析結果**
* 建立互動式 **Streamlit 視覺化介面**

---

## 🧠 核心功能

### 🔍 1. Google Drive 檔案監控

* 透過 Google Drive API 讀取檔案資料
* 分析檔案權限與分享對象

---

### 🚨 2. DLP 偵測機制

系統可偵測以下風險行為：

* 外部帳號分享（External Sharing）
* Anyone with link 公開存取
* 外部使用者具有編輯權限

---

### 📊 3. 風險評分系統（Risk Score）

| 條件                  | 分數  |
| ------------------- | --- |
| 分享給外部帳號             | +40 |
| 開啟 Anyone with link | +50 |
| 外部使用者可編輯            | +25 |
| 含敏感關鍵字              | +20 |
| 無法讀取權限（風險不明）        | +10 |

風險等級：

* **High（高風險）**：≥ 71
* **Medium（中風險）**：31–70
* **Low（低風險）**：≤ 30

---

### 🤖 4. 可解釋 AI（xAI）

系統可提供自然語言分析說明：

* 為什麼該文件具有風險
* 可能造成的影響
* 建議的處理方式

---

### 🖥️ 5. Streamlit 視覺化介面

* 即時顯示掃描結果
* 高風險檔案標示
* 統計摘要（外部分享數量等）
* CSV 匯出功能

---

## 🏗️ 系統架構

```text
Google Drive
     ↓
Google Drive API
     ↓
Python DLP 分析引擎
     ↓
風險評分（Rule-based）
     ↓
Streamlit Dashboard
     ↓
使用者 / 管理者
```

---

## ⚙️ 安裝方式

### 1️⃣ 下載專案

```bash
git clone https://github.com/your-username/drive-dlp-project.git
cd drive-dlp-project
```

---

### 2️⃣ 安裝套件

```bash
pip install -r requirements.txt
```

---

### 3️⃣ 設定憑證

將 Google OAuth 憑證放入專案目錄：

```text
credentials.json
```

---

## ▶️ 使用方式

### 啟動系統

```bash
streamlit run app.py
```

---

### 第一次使用

* 登入 Google Workspace 帳號
* 授權存取 Google Drive

---

## 📂 輸出結果

系統會產生：

```text
dlp_scan_results.csv
```

包含欄位：

* 檔案名稱
* 擁有者
* 分享狀態
* 外部使用者
* 風險分數
* 風險等級
* 風險原因

---

## 🔐 資安設計說明

* 使用 OAuth 2.0 驗證
* 不直接公開 Google Drive 資料
* 系統於本機執行（避免外部存取風險）

---

## 📊 應用情境

* 偵測誤分享文件
* 企業內部資料外洩監控
* 資安稽核輔助工具
* xAI 可解釋分析展示

---

## 🚀 未來擴充

* 即時監控（Webhook / API）
* Google Workspace Studio 整合
* 自動通知（Email / Chat）
* 機器學習異常偵測

---

## 👩‍💻 作者

Monica

---

## 📄 授權

本專案僅供學術與教學用途。
