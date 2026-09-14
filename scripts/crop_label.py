from PIL import Image
import numpy as np

img = Image.open(r'C:\Users\Charwiz43\.gemini\antigravity-ide\brain\ba7a71ce-2181-49cb-81d8-b46566a49aa0\.user_uploaded\media_1786679918824.png')
# Let's crop the label region (280, 450, 750, 860) and inspect
label_crop = img.crop((290, 460, 735, 860))
label_crop.save(r'C:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026\label_crop.png')
print("Saved label crop.")
