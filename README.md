# Logo Placement Analyzer

AI-powered logo placement system that finds optimal corner positions in images and automatically places logos while avoiding text and important visual elements.

## Features

- **Smart Corner Analysis**: Uses OCR and edge detection to find the best logo placement
- **Contrast-Based Logo Selection**: Automatically chooses dark/light logo variants based on background
- **S3 Integration**: Direct upload to S3 with automatic original image cleanup
- **Bias System**: Prefers bottom corners for better visual hierarchy
- **High-Quality Processing**: Preserves image quality and transparency

## Quick Start

### System Requirements

- Python 3.12+
- Tesseract OCR 5.5+
- AWS credentials configured

### Installation

```bash
# Clone the repository
git clone https://github.com/karatechopping/buylocal-logoplacement.git
cd buylocal-logoplacement

# Install system dependencies (Ubuntu)
sudo add-apt-repository ppa:alex-p/tesseract-ocr-devel -y
sudo apt update && sudo apt install -y tesseract-ocr

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure AWS credentials (BuyLocalNZ profile required)
aws configure --profile BuyLocalNZ
```

### Usage

**Start Development Server:**
```bash
python app.py
```

**Production Deployment:**
```bash
sudo ./deploy.sh
```

**API Example:**
```bash
curl -X POST http://localhost:5001/analyze-placement \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.png",
    "dark_logo_url": "https://example.com/logo-dark.png", 
    "light_logo_url": "https://example.com/logo-light.png"
  }'
```

## API Reference

### POST /analyze-placement

**Required Parameters:**
- `image_url` - Source image URL (S3 supported)
- `dark_logo_url` - Dark logo variant URL  
- `light_logo_url` - Light logo variant URL

**Optional Parameters:**
- `return_image` - Create composite image (default: true)
- `upload_to_s3` - Upload to S3 vs local storage (default: true)
- `delete_original` - Delete original image after processing (default: true)

**Response:**
```json
{
  "status": "successful",
  "placement": {
    "corner": "bottom-left",
    "x": 25, "y": 849,
    "width": 150, "height": 150
  },
  "selected_logo": "https://example.com/logo-light.png",
  "output_image": "https://bucket.s3.amazonaws.com/path/image-logo.png",
  "original_deleted": true
}
```

## How It Works

1. **Corner Analysis**: Divides image into 4 corner regions and analyzes each for:
   - Text content (OCR detection)
   - Visual complexity (edge density)
   - Available space

2. **Smart Ranking**: Applies bias system favoring bottom corners:
   - Bottom-right: +25% bonus
   - Bottom-left: +15% bonus  
   - Top-right: +5% bonus
   - Top-left: no bonus

3. **Logo Selection**: Analyzes background brightness to choose appropriate logo variant

4. **Quality Composite**: Creates high-quality composite maintaining transparency and aspect ratios

## Architecture

- **Flask API** with systematic error handling
- **OpenCV** for image processing and edge detection
- **Tesseract OCR** for text detection
- **PIL** for high-quality image compositing
- **boto3** for S3 operations
- **systemd** service for production deployment

## Deployment

The system includes automated deployment with:
- System dependency installation (Tesseract OCR)
- Virtual environment setup
- systemd service configuration
- Automatic service restart on boot

See `DEPLOYMENT.md` for detailed deployment instructions.

## Development

For development guidance and API examples, see `CLAUDE.md`.

## License

Private repository - All rights reserved.