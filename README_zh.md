# Line 照片自動旋轉機器人

[English](README.md) | [繁體中文](README_zh.md)

收到照片時，若文字方向與照片方向不符，自動旋轉後回傳。

---

## 專案結構

```
line-bot/
├── app.py            # 主程式
├── requirements.txt  # Python 套件
├── Dockerfile        # Docker 部署設定
├── render.yaml       # Render 部署設定
├── README.md         # 英文文件
└── README_zh.md      # 中文文件
```

---

## 環境變數（必填）

| 變數名稱                    | 說明                | 取得方式                |
| --------------------------- | ------------------- | ----------------------- |
| `LINE_CHANNEL_ACCESS_TOKEN` | Line Bot Token      | Line Developers Console |
| `LINE_CHANNEL_SECRET`       | Line Channel Secret | Line Developers Console |

---

## 本機測試步驟

### 1. 安裝 Tesseract OCR

**macOS**

```bash
brew install tesseract tesseract-lang
```

**Ubuntu / Debian**

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-tra tesseract-ocr-chi-sim
```

**Windows**
下載安裝包：https://github.com/UB-Mannheim/tesseract/wiki

### 2. 安裝 uv（若尚未安裝）

**macOS / Linux**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. 建立虛擬環境並安裝套件

```bash
uv venv                        # 建立 .venv 虛擬環境
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 4. 設定環境變數

```bash
export LINE_CHANNEL_ACCESS_TOKEN="你的Token"
export LINE_CHANNEL_SECRET="你的Secret"
```

### 5. 啟動伺服器

```bash
python app.py
```

### 6. 用 ngrok 開啟公開網址（測試用）

```bash
ngrok http 5000
```

把 `https://xxxx.ngrok.io/webhook` 填入 Line Developers Console 的 Webhook URL。

---

## 部署到 Render（免費）

1. 把這個資料夾推上 GitHub
2. 在 [Render](https://render.com/) 建立 **New Web Service**，連結 GitHub repo
3. Render 會自動讀取 `render.yaml` 建立 Docker 容器（自動安裝 Tesseract OCR 等依賴）
4. 在 Render Dashboard → Environment 填入兩個 LINE 環境變數
5. 部署完成後，把 `https://your-app.onrender.com/webhook` 填入 Line Developers Console

---

## 運作流程

```
使用者傳送照片
       │
       ▼
  Tesseract OSD 偵測文字方向
       │
  文字是否需要旋轉（90°/180°/270°）？──否──► 回傳：無需旋轉
       │
      是
       │
       ▼
  Line 顯示 Loading 動畫
       │
       ▼
  Pillow 旋轉圖片並暫存於本機伺服器
       │
       ▼
  Line 回傳旋轉後照片（附上旋轉角度與本機 URL）
       │
       ▼
  30秒後自動刪除本機暫存圖片
```

---

## 常見問題

**Q: Tesseract 偵測不準怎麼辦？**
可調整 `app.py` 中的 `confidence < 1.5` 閾值，數字越高越嚴格。

**Q: 圖片暫存如何處理？**
程式會直接在伺服器上產生並保存暫存圖片（透過 `/images/<filename>` 提供給 LINE 讀取），並在 30 秒後自動刪除，無需依賴外部圖床。

**Q: 支援中文 OCR 嗎？**
支援。`render.yaml` 已安裝 `tesseract-ocr-chi-tra`（繁中）和 `tesseract-ocr-chi-sim`（簡中）。
