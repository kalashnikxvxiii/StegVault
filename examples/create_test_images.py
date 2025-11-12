"""
Create test images for StegVault examples.
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np


def create_gradient_image(filename, size=(500, 500)):
    """Create a gradient image for testing."""
    img = Image.new('RGB', size)
    draw = ImageDraw.Draw(img)

    for y in range(size[1]):
        # Create gradient from blue to purple
        r = int((y / size[1]) * 200)
        g = int((y / size[1]) * 100)
        b = 200
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))

    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()

    text = "StegVault Test Image"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    draw.text(position, text, fill=(255, 255, 255), font=font)

    img.save(filename, 'PNG')
    print(f"Created: {filename}")


def create_pattern_image(filename, size=(500, 500)):
    """Create a geometric pattern image."""
    img = Image.new('RGB', size, color=(50, 50, 50))
    draw = ImageDraw.Draw(img)

    # Draw squares
    square_size = 50
    for i in range(0, size[0], square_size):
        for j in range(0, size[1], square_size):
            if (i // square_size + j // square_size) % 2 == 0:
                draw.rectangle(
                    [i, j, i + square_size, j + square_size],
                    fill=(100, 150, 200)
                )

    img.save(filename, 'PNG')
    print(f"Created: {filename}")


def create_nature_image(filename, size=(500, 500)):
    """Create a nature-inspired image with noise."""
    # Create base with gradient
    img_array = np.zeros((size[1], size[0], 3), dtype=np.uint8)

    # Sky gradient (top half)
    for y in range(size[1] // 2):
        progress = y / (size[1] // 2)
        img_array[y, :] = [
            int(135 + progress * 50),  # R
            int(206 - progress * 50),  # G
            int(235 - progress * 20)   # B
        ]

    # Ground (bottom half)
    for y in range(size[1] // 2, size[1]):
        img_array[y, :] = [34, 139, 34]  # Forest green

    # Add some random noise for texture
    noise = np.random.randint(-20, 20, (size[1], size[0], 3), dtype=np.int16)
    img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    img = Image.fromarray(img_array)
    img.save(filename, 'PNG')
    print(f"Created: {filename}")


if __name__ == '__main__':
    print("Creating test images for StegVault examples...")
    print("-" * 50)

    create_gradient_image('cover_gradient.png')
    create_pattern_image('cover_pattern.png')
    create_nature_image('cover_nature.png')

    print("-" * 50)
    print("Done! Test images created successfully.")
    print("\nThese images can be used with StegVault to hide encrypted passwords.")
