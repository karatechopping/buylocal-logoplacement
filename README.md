# Logo Placement Analyzer

AI-powered logo placement analysis that finds optimal corner positions and selects appropriate logo variants based on contrast analysis.

## Features

- **Corner Analysis**: Identifies the best corner for logo placement
- **Text Detection**: Avoids placing logos over text content
- **Contrast Optimization**: Selects dark/light logo variant for maximum contrast
- **REST API**: Callable via curl with image and logo URLs

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Start the server
```bash
python app.py
```

### API Endpoint

**POST /analyze-placement**

Parameters:
- `image_url`: URL to the main image
- `dark_logo_url`: URL to the dark logo variant
- `light_logo_url`: URL to the light logo variant

### Example curl command

```bash
curl -X POST http://localhost:5000/analyze-placement \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "dark_logo_url": "https://example.com/logo-dark.png",
    "light_logo_url": "https://example.com/logo-light.png"
  }'
```

### Response Format

```json
{
  "placement": {
    "corner": "top-right",
    "x": 450,
    "y": 50,
    "width": 100,
    "height": 50
  },
  "selected_logo": "https://example.com/logo-dark.png",
  "confidence": 0.85,
  "background_brightness": 180,
  "contrast_ratio": 0.7,
  "analysis_details": {
    "has_text": false,
    "edge_density": 0.05,
    "space_sufficient": true
  }
}
```

## Health Check

```bash
curl http://localhost:5000/health
```