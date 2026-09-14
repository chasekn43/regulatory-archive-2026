import os
from PIL import Image, ImageDraw, ImageFont

def perfect_parody_jug():
    src_path = r"C:\Users\Charwiz43\.gemini\antigravity-ide\brain\ba7a71ce-2181-49cb-81d8-b46566a49aa0\.user_uploaded\media_1786679918824.png"
    img = Image.open(src_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    font_dir = r"C:\Windows\Fonts"
    font_arial_narrow_title = ImageFont.truetype(os.path.join(font_dir, "ARIALNB.TTF"), 54)
    font_arial_bold_sm = ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 14)
    font_arial_bold_xs = ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 10)
    font_arial_italic = ImageFont.truetype(os.path.join(font_dir, "ariali.ttf"), 9)
    font_arial_bi = ImageFont.truetype(os.path.join(font_dir, "arialbi.ttf"), 13.5)
    font_arial_reg = ImageFont.truetype(os.path.join(font_dir, "arial.ttf"), 12)
    font_arial_reg_sm = ImageFont.truetype(os.path.join(font_dir, "arial.ttf"), 10)
    font_arialnb_med = ImageFont.truetype(os.path.join(font_dir, "ARIALNB.TTF"), 10.5)

    # 1. Clean Top White Banner [298, 460, 727, 545]
    draw.rectangle([298, 460, 727, 545], fill=(255, 255, 255, 255))

    # Top Left FTA Logo block
    draw.text((310, 468), "FTA", font=font_arial_narrow_title, fill=(120, 20, 40, 255))
    draw.text((395, 476), "®", font=font_arial_bold_xs, fill=(120, 20, 40, 255))
    draw.text((310, 528), "World Class Debt Solutions®", font=ImageFont.truetype(os.path.join(font_dir, "arialbi.ttf"), 10), fill=(120, 20, 40, 255))

    # Top Right Icon Box
    draw.rectangle([635, 466, 715, 528], fill=(245, 248, 255, 255), outline=(24, 69, 138, 255), width=2)
    draw.text((642, 474), "💸", font=ImageFont.truetype(os.path.join(font_dir, "seguiemj.ttf"), 18), fill=(0, 0, 0, 255))
    draw.text((642, 498), "47% LATE", font=ImageFont.truetype(os.path.join(font_dir, "ARIALNB.TTF"), 10), fill=(180, 20, 20, 255))
    draw.text((638, 532), "Liquidity Drainer", font=font_arial_italic, fill=(24, 69, 138, 255))

    # 2. Main Blue Container [298, 545, 727, 852]
    BLUE_COLOR = (24, 69, 138, 255)
    draw.rectangle([298, 545, 727, 852], fill=BLUE_COLOR)

    # Title: Affirm™
    draw.text((312, 552), "Affirm", font=font_arial_narrow_title, fill=(255, 255, 255, 255))
    draw.text((440, 560), "TM", font=font_arial_bold_sm, fill=(255, 255, 255, 255))

    # Subtitle
    draw.text((312, 612), "Subprime Liquidity Drain & Balance Sheet Sanitizer", font=font_arial_bi, fill=(255, 255, 255, 255))

    # Formula Description
    desc_line1 = "Lotionized formula is ultra mild to credit reporting bureaus. Fortified with"
    desc_line2 = "35.99% APR and 36-month installment cycles; helps prevent the spread of"
    desc_line3 = "transparent underwriting, ability-to-pay checks, and consumer liquidity."
    draw.text((312, 638), desc_line1, font=font_arial_reg, fill=(255, 255, 255, 255))
    draw.text((312, 654), desc_line2, font=font_arial_reg, fill=(255, 255, 255, 255))
    draw.text((312, 670), desc_line3, font=font_arial_reg, fill=(255, 255, 255, 255))

    # Warning Box
    warn_line1 = "WARNING: CAUSES SYSTEMIC GHOST DEBT & $35 BANK OVERDRAFT FEES."
    warn_line2 = "ATENCIÓN: CAUSA MOROSIDAD, APILAMIENTO DE DEUDAS Y CARGOS POR SOBREGIRO."
    warn_sub = "See SEC Form 10-K & D.C. District Court (Case 1:24-cv-02966) for additional side effects."
    net_contents = "NET CONTENTS: ~$36 BILLION GMV / 47% DELINQUENT"

    draw.text((312, 702), warn_line1, font=font_arialnb_med, fill=(255, 255, 255, 255))
    draw.text((312, 716), warn_line2, font=ImageFont.truetype(os.path.join(font_dir, "ARIALNB.TTF"), 8), fill=(255, 255, 255, 255))
    draw.text((312, 728), warn_sub, font=font_arial_reg_sm, fill=(210, 230, 255, 255))
    draw.text((312, 746), net_contents, font=ImageFont.truetype(os.path.join(font_dir, "ARIALNB.TTF"), 10.5), fill=(255, 255, 255, 255))

    # Company Footer Information
    draw.text((312, 775), "Financial Technology Laboratories, Inc.", font=ImageFont.truetype(os.path.join(font_dir, "arialbd.ttf"), 12), fill=(255, 255, 255, 255))
    draw.text((312, 792), "San Francisco, CA • Reg. Z Exemption Division", font=font_arial_reg_sm, fill=(220, 235, 255, 255))
    draw.text((312, 807), "www.ghostdebt.com • (800) NO-TILA", font=font_arial_reg_sm, fill=(220, 235, 255, 255))

    # Product No
    draw.text((585, 807), "Product No.: 15-USC-1602G", font=font_arial_reg_sm, fill=(220, 235, 255, 255))

    # Save
    artifact_path = r"C:\Users\Charwiz43\.gemini\antigravity-ide\brain\ba7a71ce-2181-49cb-81d8-b46566a49aa0\affirm_jug_parody.png"
    workspace_path = r"c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026\affirm_jug_parody.png"
    
    img.save(artifact_path)
    img.save(workspace_path)
    print("Perfect parody image saved.")

if __name__ == "__main__":
    perfect_parody_jug()
