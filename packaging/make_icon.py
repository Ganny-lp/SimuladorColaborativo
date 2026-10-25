"""Gera packaging/icon.ico a partir da marca do app (requer Pillow, já vem com o Streamlit)."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "frontend" / "assets" / "brand" / "lumina_mark.png"
DST = Path(__file__).resolve().parent / "icon.ico"

img = Image.open(SRC).convert("RGBA")
side = max(img.size)
canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
canvas.save(DST, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"Ícone gerado: {DST}")
