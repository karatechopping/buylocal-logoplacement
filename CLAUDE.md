# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered logo placement analyzer that finds optimal corner positions in images and selects appropriate logo variants based on contrast analysis. The system uploads composite images directly to S3.

## Development Setup

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### AWS Configuration
The application uses the `BuyLocalNZ` AWS profile from `~/.aws/credentials`. Ensure this profile exists with appropriate S3 permissions for the buylocalnz bucket.

### Running the Application

**Development:**
```bash
# Start development server (runs on port 5001)
python app.py
```

**Production Deployment:**
```bash
# Deploy with systemd service
sudo ./deploy.sh

# Manual service management
sudo systemctl start logo-analyzer
sudo systemctl stop logo-analyzer
sudo systemctl status logo-analyzer
sudo journalctl -u logo-analyzer -f  # View logs
```

**Testing:**
```bash
# Test API health
curl http://localhost:5001/health

# Test placement analysis (minimal - uses defaults)
curl -X POST http://localhost:5001/analyze-placement \
  -H "Content-Type: application/json" \
  -d '{"image_url":"https://buylocalnz.s3.amazonaws.com/QNTM/SMPostImages/bk-test-1751683140376.png","dark_logo_url":"https://buylocalnz.s3.amazonaws.com/QNTM/Logos/qntmlogoblack.png","light_logo_url":"https://buylocalnz.s3.amazonaws.com/QNTM/Logos/qntmlogo.png"}'

# Test with local storage only
curl -X POST http://localhost:5001/analyze-placement \
  -H "Content-Type: application/json" \
  -d '{"image_url":"https://buylocalnz.s3.amazonaws.com/QNTM/SMPostImages/bk-test-1751683140376.png","dark_logo_url":"https://buylocalnz.s3.amazonaws.com/QNTM/Logos/qntmlogoblack.png","light_logo_url":"https://buylocalnz.s3.amazonaws.com/QNTM/Logos/qntml

.png","upload_to_s3":false}'

# Test analysis only (no image creation)
curl -X POST http://localhost:5001/analyze-placement \
  -H "Content-Type: application/json" \
  -d '{"image_url":"https://buylocalnz.s3.amazonaws.com/QNTM/SMPostImages/bk-test-1751683140376.png","dark_logo_url":"https://buylocalnz.s3.amazonaws.com/QNTM/Logos/qntml

black.png","light_logo_url":"https://buylocalnz.s3.amazonaws.com/QNTM/Logos/qntml

.png","return_image":false}'
```

### Testing and Utilities
```bash
# Run API test script
python test_api.py

# Clean up local output files
./cleanup.sh all
./cleanup.sh outputs/output_abc123.png
```

## Architecture

### Core Components

**LogoPlacementAnalyzer Class**
- Main analysis engine with configurable margins (25px preferred, 12px minimum)
- Uses BuyLocalNZ AWS profile for S3 operations
- Handles image download, analysis, and composite creation

**Corner Analysis Pipeline**
1. Divides image into 4 corner regions (each 1/3 of image dimensions)
2. Analyzes each corner for text (OCR), visual complexity (edge density), and available space
3. Applies 15% suitability bonus to bottom corners (bottom-preferred bias)
4. Ranks corners by suitability score

**Logo Selection Logic**
- Downloads and detects actual logo dimensions (not hardcoded)
- Calculates average brightness in placement area
- Selects dark logo for bright backgrounds, light logo for dark backgrounds
- Preserves aspect ratio during resizing if significantly different from target

**S3 Integration**
- Parses S3 URLs to extract bucket and key
- Uploads composite images with `-logo` suffix to same location as original
- Falls back to local file storage if S3 upload fails

### API Response Format

**Success Response:**
```json
{
  "status": "successful",
  "reason": null,
  "placement": {
    "corner": "bottom-left",
    "x": 25, "y": 849,
    "width": 150, "height": 150
  },
  "selected_logo": "https://example.com/logo-light.png",
  "output_image": "https://bucket.s3.amazonaws.com/path/image-logo.png"
}
```

**Failure Response:**
```json
{
  "status": "failed",
  "reason": "Insufficient space in best corner (top-right). Available: 100x80, Required: 150x150",
  "placement": null,
  "selected_logo": null,
  "output_image": null
}
```

### Key Configuration

- **Margins**: 25px preferred, 12px minimum on each side
- **Server Port**: 5001 (5000 conflicts with macOS AirPlay)
- **Corner Regions**: Each corner is 1/3 of image width/height
- **Bottom Bias**: 15% suitability multiplier for bottom corners
- **Confidence Threshold**: 0.3 minimum for successful placement

## Image Processing Pipeline

1. **Download**: Images downloaded via requests, converted to numpy arrays
2. **Analysis**: OCR text detection, edge density calculation, space measurement
3. **Composite Creation**: Direct PIL processing to preserve transparency and quality
4. **Upload**: S3 upload to same bucket/folder with `-logo` suffix

The system automatically detects logo dimensions and maintains aspect ratio to prevent distortion during placement.