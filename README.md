# Line 照片自動旋轉機器人

收到直式照片時，若文字方向與照片方向不符，自動旋轉後回傳。

---

## 專案結構

```
line-bot/
├── app.py            # 主程式
├── requirements.txt  # Python 套件
├── render.yaml       # Render 部署設定
└── README.md
```

---

## 環境變數（必填）

| 變數名稱                    | 說明                | 取得方式                |
| --------------------------- | ------------------- | ----------------------- |
| `LINE_CHANNEL_ACCESS_TOKEN` | Line Bot Token      | Line Developers Console |
| `LINE_CHANNEL_SECRET`       | Line Channel Secret | Line Developers Console |
| `IMGBB_API_KEY`             | 圖片上傳用 API Key  | https://api.imgbb.com/  |

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
export IMGBB_API_KEY="你的imgbb金鑰"
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
3. Render 會自動讀取 `render.yaml`
4. 在 Render Dashboard → Environment 填入三個環境變數
5. 部署完成後，把 `https://your-app.onrender.com/webhook` 填入 Line Developers Console

---

## 運作流程

```
使用者傳送照片
       │
       ▼
  是直式照片？──否──► 忽略
       │
      是
       │
       ▼
  Tesseract OSD 偵測文字方向
       │
  文字是否橫躺（90°/270°）？──否──► 忽略
       │
      是
       │
       ▼
  Pillow 旋轉圖片
       │
       ▼
  上傳至 imgbb 取得公開 URL
       │
       ▼
  Line reply_message 回傳旋轉後照片
```

---

## 常見問題

**Q: Tesseract 偵測不準怎麼辦？**
可調整 `app.py` 中的 `confidence < 1.5` 閾值，數字越高越嚴格。

**Q: 可以換掉 imgbb 嗎？**
可以，把 `upload_image_to_imgbb()` 換成 AWS S3、Google Cloud Storage 或任何能產生公開 URL 的服務。

**Q: 支援中文 OCR 嗎？**
支援。`render.yaml` 已安裝 `tesseract-ocr-chi-tra`（繁中）和 `tesseract-ocr-chi-sim`（簡中）。
