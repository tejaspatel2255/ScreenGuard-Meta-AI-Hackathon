from PIL import Image, ImageDraw, ImageFont
import io

img = Image.new("RGB", (1024, 600), color=(240, 244, 248))
draw = ImageDraw.Draw(img)

# Draw simulated webpage header
draw.rectangle([0, 0, 1024, 70], fill=(41, 128, 185))
draw.text((30, 25), "Acme Admin - Customer Refund Portal", fill=(255, 255, 255))

# Draw form
draw.rectangle([100, 120, 924, 480], fill=(255, 255, 255), outline=(200, 200, 200), width=2)
draw.text((140, 150), "Transaction ID: TX-984321", fill=(30, 30, 30))
draw.text((140, 200), "Customer Name: John Doe", fill=(30, 30, 30))
draw.text((140, 250), "Refund Amount: $45.00", fill=(30, 30, 30))

# Draw Submit Refund Button
draw.rectangle([140, 330, 320, 380], fill=(46, 204, 113))
draw.text((170, 345), "Submit Refund", fill=(255, 255, 255))

# Draw Confirmation Banner
draw.rectangle([140, 410, 880, 460], fill=(235, 247, 238), outline=(46, 204, 113), width=1)
draw.text((160, 425), "SUCCESS: Refund has been authorized and processed.", fill=(39, 174, 96))

img.save("sample_screen.png", format="PNG")
print("Generated sample_screen.png")
