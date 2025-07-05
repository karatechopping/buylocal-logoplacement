# Deployment Requirements

## System Dependencies

The application requires Tesseract OCR 5.5+ to be installed at the system level for text detection functionality.

### Ubuntu/Debian
For optimal compatibility, use the tesseract-ocr-devel PPA to get the latest version:
```bash
sudo add-apt-repository ppa:alex-p/tesseract-ocr-devel -y
sudo apt update
sudo apt install -y tesseract-ocr
```

### macOS
```bash
brew install tesseract
```

## Python Dependencies

Install Python requirements in virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Notes

- `pytesseract` in requirements.txt is only the Python wrapper
- The actual `tesseract` binary must be installed separately at system level
- Without tesseract, text detection will fail silently and logo placement will be suboptimal