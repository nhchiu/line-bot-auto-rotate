import os
import io
import math
import logging
from flask import Flask, request, abort
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    ImageMessage,
    ShowLoadingAnimationRequest,
    TextMessage,
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    MessageEvent,
    ImageMessageContent,
)
from PIL import Image
import pytesseract
from pytesseract import Output
import requests

# For Windows, point pytesseract to the tesseract executable if it's not in PATH
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ── logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Flask & Line SDK ──────────────────────────────────────────────────────────
app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET       = os.environ["LINE_CHANNEL_SECRET"]

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
line_bot_api_blob = MessagingApiBlob(api_client)

handler = WebhookHandler(LINE_CHANNEL_SECRET)


# ── helpers ───────────────────────────────────────────────────────────────────

def get_dominant_text_angle(img: Image.Image) -> float | None:
    """
    Run Tesseract OSD (Orientation & Script Detection) on the image.
    Returns the detected rotation angle (0, 90, 180, 270) or None if
    Tesseract cannot determine an orientation confidently.
    """
    try:
        osd = pytesseract.image_to_osd(img, output_type=Output.DICT)
        angle     = osd.get("rotate", 0)          # degrees Tesseract wants to rotate
        confidence= osd.get("orientation_conf", 0)
        logger.info(f"OSD → rotate={angle}°, confidence={confidence:.2f}")
        if confidence < 1.5:                       # low-confidence → skip
            return None
        return angle
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract is not installed or not in PATH.")
        raise
    except Exception as e:
        logger.warning(f"OSD failed: {e}")
        return None


def needs_rotation(img: Image.Image) -> int:
    """
    Returns the number of degrees (90, 180, or 270) we should rotate the
    image so that its text reads upright, or 0 if no rotation is needed.

    Tesseract OSD 'rotate' = how many CCW degrees you must rotate the *image*
    to make the text upright.  Pillow's Image.rotate() is also CCW.

    We only act when Tesseract says 90, 180, or 270.
    """
    angle = get_dominant_text_angle(img)
    if angle is None:
        return 0
    angle = int(angle) % 360
    
    if angle == 90:
        return 270
    elif angle == 270:
        return 90
    elif angle == 180:
        return 180
        
    return 0


def rotate_image(img: Image.Image, degrees: int) -> Image.Image:
    """Rotate counter-clockwise, expanding the canvas so nothing is cropped."""
    return img.rotate(degrees, expand=True)


def image_to_bytes(img: Image.Image, fmt: str = "JPEG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=92)
    return buf.getvalue()


def upload_image_to_imgbb(image_bytes: bytes) -> str:
    """
    Upload image to imgbb (free, no auth needed for small files) and return
    the public URL.  Replace this with your own storage (S3, GCS, etc.)
    if you prefer.

    ⚠️  Set IMGBB_API_KEY in your environment variables.
        Get a free key at https://api.imgbb.com/
    """
    api_key = os.environ.get("IMGBB_API_KEY", "")
    if not api_key:
        raise RuntimeError("IMGBB_API_KEY is not set.")

    import base64
    b64 = base64.b64encode(image_bytes).decode()
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        # Note: 60s is the minimum expiration allowed by ImgBB API
        data={"key": api_key, "image": b64, "expiration": 60},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]["url"]


# ── webhook ───────────────────────────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body      = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature.")
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event: MessageEvent):
    """Core logic: receive image → OCR → rotate if needed → reply."""

    # 0. Show loading animation
    if hasattr(event.source, "user_id"):
        try:
            line_bot_api.show_loading_animation(
                ShowLoadingAnimationRequest(
                    chat_id=event.source.user_id,
                    loading_animation_duration=20
                )
            )
        except Exception as e:
            logger.warning(f"Failed to show loading animation: {e}")

    # 1. Download original image from Line servers
    raw = line_bot_api_blob.get_message_content(event.message.id)
    img = Image.open(io.BytesIO(raw)).convert("RGB")

    logger.info(f"Received image {img.width}×{img.height}")

    # 2. Check whether text direction matches image orientation
    degrees = needs_rotation(img)

    if degrees == 0:
        logger.info("Text direction matches image — no action taken.")
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text="The image does not need to be rotated.")
                ]
            )
        )
        return

    # 4. Rotate and send back
    logger.info(f"Rotating image by {degrees}° CCW…")
    rotated       = rotate_image(img, degrees)
    rotated_bytes = image_to_bytes(rotated)

    # Upload to a public host so Line can fetch it
    public_url = upload_image_to_imgbb(rotated_bytes)
    logger.info(f"Uploaded rotated image → {public_url}")

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text=f"The image was rotated by {degrees} degrees."),
                ImageMessage(
                    original_content_url=public_url,
                    preview_image_url=public_url,
                )
            ]
        )
    )


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
