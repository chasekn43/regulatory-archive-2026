from PIL import Image, ImageDraw, ImageFont
import numpy as np

img = Image.open(r'C:\Users\Charwiz43\.gemini\antigravity-ide\brain\ba7a71ce-2181-49cb-81d8-b46566a49aa0\.user_uploaded\media_1786679918824.png')
print("Image size:", img.size)

# Let's inspect the blue color of the label
# The blue box is roughly in the middle
arr = np.array(img)
# Find where the blue label is
# Blue is roughly R < 50, G < 80, B > 120
blue_mask = (arr[:, :, 0] < 60) & (arr[:, :, 1] < 100) & (arr[:, :, 2] > 100) & (arr[:, :, 3] > 200)
y_indices, x_indices = np.where(blue_mask)
print(f"Blue box X range: {x_indices.min()} to {x_indices.max()}")
print(f"Blue box Y range: {y_indices.min()} to {y_indices.max()}")
