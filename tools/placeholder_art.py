"""把美術換成色塊,方便改玩法時先不管美術。尺寸跟原圖一樣,AtlasTexture / TileSet 的座標都不用動。

    python tools/placeholder_art.py

- 角色 / 武器 / 掉落物(16×16 單張):原圖不透明區域的外框,填固定的辨識色 + 深色描邊
- 圖集(tilemap_packed.png、ui.png):每 16×16 一格各自處理;幾乎填滿的格子整格填平均色,
  其他格子畫外框色塊
- screen_transition.png(轉場 shader 用的遮罩)和 icon_large.png 不動

原圖都還在 git 歷史裡:git log --diff-filter=M -- '*.png' 找換色塊之前那個 commit 就能拿回來。
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
CELL = 16
ALPHA_MIN = 16

# 一眼分得出誰是誰比像原圖重要
SPRITE_COLORS = {
    "scenes/game_object/player/player.png": (66, 135, 245),
    "scenes/game_object/basic_enemy/basic_enemy.png": (80, 190, 90),
    "scenes/game_object/bat_enemy/bat_enemy.png": (160, 90, 210),
    "scenes/game_object/wizard_enemy/wizard_enemy.png": (225, 70, 70),
    "scenes/game_object/experience_vial/experience_vial.png": (60, 220, 220),
    "scenes/abilities/sword_ability/sword.png": (235, 235, 235),
    "scenes/abilities/axe_ability/axe.png": (245, 170, 60),
    "scenes/abilities/anvil_ability/tile_0074.png": (130, 130, 140),
    "scenes/abilities/anvil_ability/particle.png": (200, 200, 200),
}
ATLASES = ["assets/environment/tilemap_packed.png", "assets/ui/ui.png"]


def _opaque(img: Image.Image) -> list:
    return [p for p in img.getdata() if p[3] > ALPHA_MIN]


def _block(draw: ImageDraw.ImageDraw, box, color, offset=(0, 0)) -> None:
    x0, y0, x1, y1 = box
    ox, oy = offset
    border = tuple(v // 3 for v in color) + (255,)
    draw.rectangle([ox + x0, oy + y0, ox + x1 - 1, oy + y1 - 1], fill=tuple(color) + (255,), outline=border)


def sprite(rel: str, color) -> None:
    path = ROOT / rel
    img = Image.open(path).convert("RGBA")
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bbox = img.getchannel("A").point(lambda a: 255 if a > ALPHA_MIN else 0).getbbox()
    if bbox:
        _block(ImageDraw.Draw(out), bbox, color)
    out.save(path)


def atlas(rel: str) -> None:
    path = ROOT / rel
    img = Image.open(path).convert("RGBA")
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(out)
    for y in range(0, img.height, CELL):
        for x in range(0, img.width, CELL):
            cell = img.crop((x, y, x + CELL, y + CELL))
            opaque = _opaque(cell)
            if not opaque:
                continue
            color = tuple(sum(p[i] for p in opaque) // len(opaque) for i in range(3))
            if len(opaque) > CELL * CELL * 0.9:
                draw.rectangle([x, y, x + CELL - 1, y + CELL - 1], fill=color + (255,))
            else:
                bbox = cell.getchannel("A").point(lambda a: 255 if a > ALPHA_MIN else 0).getbbox()
                _block(draw, bbox, color, (x, y))
    out.save(path)


if __name__ == "__main__":
    for rel, color in SPRITE_COLORS.items():
        sprite(rel, color)
        print("sprite", rel)
    for rel in ATLASES:
        atlas(rel)
        print("atlas ", rel)
