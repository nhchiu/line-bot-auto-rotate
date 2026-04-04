# Line Photo Auto-Rotate Bot

[English](README.md) | [繁體中文](README_zh.md)

When an image is received, if the text direction does not match the image orientation, it automatically rotates the image and sends it back.

---

## Project Structure

```
line-bot/
├── app.py            # Main application
├── requirements.txt  # Python packages
├── Dockerfile        # Docker deployment config
├── render.yaml       # Render deployment config
├── README.md         # English Documentation
└── README_zh.md      # Chinese Documentation
```

---

## Environment Variables (Required)

| Variable Name                 | Description                   | Where to Get It               |
| ----------------------------- | ----------------------------- | ----------------------------- |
| `LINE_CHANNEL_ACCESS_TOKEN`   | Line Bot Token                | Line Developers Console       |
| `LINE_CHANNEL_SECRET`         | Line Channel Secret           | Line Developers Console       |

---

## Local Testing Steps

### 1. Install Tesseract OCR

**macOS**

```bash
brew install tesseract tesseract-lang
```

**Ubuntu / Debian**

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-tra tesseract-ocr-chi-sim
```

**Windows**
Download the installer: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Install uv (if not already installed)

**macOS / Linux**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Create a Virtual Environment and Install Dependencies

```bash
uv venv                        # Create a .venv virtual environment
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 4. Set Environment Variables

```bash
export LINE_CHANNEL_ACCESS_TOKEN="YourToken"
export LINE_CHANNEL_SECRET="YourSecret"
```

### 5. Start the Server

```bash
python app.py
```

### 6. Expose the Local Server using ngrok (For Testing)

```bash
ngrok http 5000
```

Paste `https://xxxx.ngrok.io/webhook` into the Webhook URL in the Line Developers Console.

---

## Deploy to Render (Free)

1. Push this folder to GitHub.
2. Create a **New Web Service** on [Render](https://render.com/) and connect your GitHub repo.
3. Render will automatically read `render.yaml` and build a Docker container (which automatically installs Tesseract OCR and dependencies).
4. Fill in the two LINE environment variables in Render Dashboard → Environment.
5. After deployment is complete, paste `https://your-app.onrender.com/webhook` into the Line Developers Console.

---

## Workflow

```
User sends an image
       │
       ▼
  Tesseract OSD detects text orientation
       │
  Does the image need rotation (90°/180°/270°)? ──No──► Reply: No rotation needed
       │
      Yes
       │
       ▼
  Line displays a Loading animation
       │
       ▼
  Pillow rotates the image and saves it to the local server temporarily
       │
       ▼
  Line replies with the rotated image (includes rotation angle and local URL)
       │
       ▼
  Temporarily cached image is automatically deleted after 30 seconds
```

---

## FAQ

**Q: What if Tesseract detection is inaccurate?**
You can adjust the `confidence < 1.5` threshold in `app.py`. A higher number means stricter detection criteria.

**Q: How is image caching handled?**
The program directly generates and saves temporary images on the server (served to LINE via `/images/<filename>`), and automatically deletes them after 30 seconds, without relying on external image hosting services.

**Q: Does it support Chinese OCR?**
Yes. `render.yaml` (through Docker) already installs `tesseract-ocr-chi-tra` (Traditional Chinese) and `tesseract-ocr-chi-sim` (Simplified Chinese).
