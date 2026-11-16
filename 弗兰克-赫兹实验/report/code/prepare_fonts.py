from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont


def main():
    for path in sorted(Path("fonts").glob("*.ttf")):
        font = TTFont(path)
        builder = FontBuilder(font=font)
        if "OS/2" not in font:
            builder.setupOS2(
                sTypoAscender=font["hhea"].ascent,
                sTypoDescender=font["hhea"].descent,
                usWinAscent=max(0, font["head"].yMax),
                usWinDescent=max(0, -font["head"].yMin),
            )
        if "post" not in font:
            builder.setupPost(keepGlyphNames=False)
        font.save(path)


if __name__ == "__main__":
    main()
