# Extension Icons

The Chrome extension requires icon files in the following sizes:

- **icon16.png** - 16x16 pixels (toolbar icon)
- **icon48.png** - 48x48 pixels (extension management page)
- **icon128.png** - 128x128 pixels (Chrome Web Store)

## Creating Icons

You can create icons using:

1. **Online Tools**
   - [Canva](https://www.canva.com/) - Free design tool
   - [Figma](https://www.figma.com/) - Professional design
   - [GIMP](https://www.gimp.org/) - Free image editor

2. **Icon Design Guidelines**
   - Use the Salvavidas branding colors: `#667eea` (primary purple) and `#764ba2` (secondary purple)
   - Include a recognizable symbol (e.g., helicopter 🚁 or lifeguard icon)
   - Ensure icons are clear and visible at small sizes
   - Use transparent background (PNG with alpha channel)
   - Test at actual sizes to ensure readability

3. **Recommended Icon Content**
   - 16x16: Simple helicopter silhouette or "S" letter
   - 48x48: Helicopter with gradient background
   - 128x128: Detailed helicopter icon with "Salvavidas" text

## Temporary Icons

For development, you can use:

1. **Placeholder Images**
   - Create solid color squares with text
   - Use online icon generators

2. **Generate with ImageMagick**
   ```bash
   # Install ImageMagick if not installed
   # Ubuntu/Debian: sudo apt-get install imagemagick
   # macOS: brew install imagemagick

   # Create simple placeholder icons
   convert -size 16x16 xc:#667eea -gravity center -pointsize 10 -fill white -annotate +0+0 "S" icon16.png
   convert -size 48x48 xc:#667eea -gravity center -pointsize 32 -fill white -annotate +0+0 "S" icon48.png
   convert -size 128x128 xc:#667eea -gravity center -pointsize 84 -fill white -annotate +0+0 "S" icon128.png
   ```

3. **Use Emoji as Placeholder**
   - Take screenshot of 🚁 emoji at different sizes
   - Crop to square and resize

## Installation Note

The extension will load without icons, but Chrome will show a default placeholder. For production use, proper icons are recommended for branding and user recognition.

## Current Status

⚠️ **Icons not included in repository**

Please create and add icon files before publishing to Chrome Web Store or sharing publicly.
