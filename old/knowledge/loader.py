import os
from bs4 import BeautifulSoup
from PIL import Image
import base64
from io import BytesIO

def load_docs_for_server(server_id: str, config: dict) -> dict:
    docs_path = config["servers"][server_id]["docs_path"]
    texts = []
    images = []

    for root, _, files in os.walk(docs_path):
        for f in files:
            if f.endswith(".html"):
                with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                    soup = BeautifulSoup(file, "lxml")
                    for script in soup(["script", "style"]):
                        script.decompose()
                    texts.append(soup.get_text(separator="\n", strip=True))
            elif f.endswith((".png", ".jpg", ".jpeg")):
                img_path = os.path.join(root, f)
                with Image.open(img_path) as img:
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    images.append(b64)

    return {
        "text": "\n\n".join(texts),
        "images": images  # Используется, если модель мультимодальная
    }