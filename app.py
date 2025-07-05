from flask import Flask, request, jsonify
import cv2
import numpy as np
from PIL import Image
import requests
import io
import pytesseract
# Set tesseract path for systemd environment
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
from urllib.parse import urlparse
import logging
import os
import uuid
import base64
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from urllib.parse import urlparse

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class LogoPlacementAnalyzer:
    def __init__(self):
        self.min_margin = 12  # Minimum 12px margin on each side
        self.preferred_margin = 25  # Preferred 25px margin on each side
        # Use BuyLocalNZ profile from ~/.aws/credentials
        session = boto3.Session(profile_name='BuyLocalNZ')
        self.s3_client = session.client('s3')
        
    def download_image(self, url):
        """Download image from URL and return as numpy array"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            return np.array(image)
        except Exception as e:
            raise ValueError(f"Failed to download image from {url}: {str(e)}")
    
    def analyze_corner_space(self, image, corner, logo_width=100, logo_height=50):
        """Analyze available space in a specific corner"""
        h, w = image.shape[:2]
        
        # Define corner regions
        corners = {
            'top-left': (0, 0, w//3, h//3),
            'top-right': (w*2//3, 0, w, h//3),
            'bottom-left': (0, h*2//3, w//3, h),
            'bottom-right': (w*2//3, h*2//3, w, h)
        }
        
        if corner not in corners:
            return None
            
        x1, y1, x2, y2 = corners[corner]
        corner_region = image[y1:y2, x1:x2]
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(corner_region, cv2.COLOR_BGR2GRAY) if len(corner_region.shape) == 3 else corner_region
        
        # Detect text using OCR
        try:
            text = pytesseract.image_to_string(gray)
            has_text = len(text.strip()) > 0
        except:
            has_text = False
        
        # Detect edges (important visual elements)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        
        # Calculate available space based on corner
        if corner == 'top-left':
            available_x = x2 - x1 - self.preferred_margin
            available_y = y2 - y1 - self.preferred_margin
            placement_x = self.preferred_margin
            placement_y = self.preferred_margin
        elif corner == 'top-right':
            available_x = x2 - x1 - self.preferred_margin
            available_y = y2 - y1 - self.preferred_margin
            placement_x = x1 + available_x - logo_width
            placement_y = self.preferred_margin
        elif corner == 'bottom-left':
            available_x = x2 - x1 - self.preferred_margin
            available_y = y2 - y1 - self.preferred_margin
            placement_x = self.preferred_margin
            placement_y = y1 + available_y - logo_height
        else:  # bottom-right
            available_x = x2 - x1 - self.preferred_margin
            available_y = y2 - y1 - self.preferred_margin
            placement_x = x1 + available_x - logo_width
            placement_y = y1 + available_y - logo_height
        
        # Check if space is sufficient
        space_sufficient = available_x >= logo_width and available_y >= logo_height
        
        # Calculate suitability score
        suitability = 1.0
        if has_text:
            suitability *= 0.3  # Heavy penalty for text
        if edge_density > 0.1:
            suitability *= (1 - edge_density)  # Penalty for high edge density
        if not space_sufficient:
            suitability *= 0.1  # Heavy penalty for insufficient space
            
        return {
            'corner': corner,
            'available_width': available_x,
            'available_height': available_y,
            'placement_x': int(placement_x),
            'placement_y': int(placement_y),
            'has_text': has_text,
            'edge_density': edge_density,
            'space_sufficient': space_sufficient,
            'suitability': suitability
        }
    
    def find_best_corner(self, image, logo_width=100, logo_height=50):
        """Find the best corner for logo placement"""
        corners = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
        results = []
        
        for corner in corners:
            result = self.analyze_corner_space(image, corner, logo_width, logo_height)
            if result:
                # Add bias for bottom corners (prefer bottom over top)
                if corner.startswith('bottom'):
                    result['suitability'] *= 1.15  # 15% bonus for bottom corners
                results.append(result)
        
        # Sort by suitability score
        results.sort(key=lambda x: x['suitability'], reverse=True)
        return results[0] if results else None
    
    def calculate_average_brightness(self, image, x, y, width, height):
        """Calculate average brightness in a specific region"""
        h, w = image.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w, x + width)
        y2 = min(h, y + height)
        
        region = image[y1:y2, x1:x2]
        
        # Convert to grayscale
        if len(region.shape) == 3:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        else:
            gray = region
            
        return np.mean(gray)
    
    def select_logo_variant(self, image, placement_x, placement_y, logo_width, logo_height):
        """Select dark or light logo based on background brightness"""
        brightness = self.calculate_average_brightness(
            image, placement_x, placement_y, logo_width, logo_height
        )
        
        # If background is bright, use dark logo; if dark, use light logo
        use_dark_logo = brightness > 127
        
        return {
            'use_dark_logo': use_dark_logo,
            'background_brightness': brightness,
            'contrast_ratio': brightness / 255 if use_dark_logo else (255 - brightness) / 255
        }
    
    def create_logo_composite(self, image, logo_url, placement_x, placement_y, logo_width, logo_height):
        """Create composite image with logo placed"""
        try:
            # Download logo
            logo_response = requests.get(logo_url, timeout=10)
            logo_response.raise_for_status()
            
            # Open logo directly with PIL to preserve quality and transparency
            pil_logo = Image.open(io.BytesIO(logo_response.content))
            
            # Convert main image to PIL
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Get original logo dimensions
            orig_logo_w, orig_logo_h = pil_logo.size
            
            # Only resize if dimensions are different (preserve original quality)
            if orig_logo_w != logo_width or orig_logo_h != logo_height:
                # Maintain aspect ratio if it's significantly different
                aspect_ratio = orig_logo_w / orig_logo_h
                target_ratio = logo_width / logo_height
                
                if abs(aspect_ratio - target_ratio) > 0.1:  # More than 10% difference
                    # Maintain aspect ratio, fit within target dimensions
                    if aspect_ratio > target_ratio:
                        new_w = logo_width
                        new_h = int(logo_width / aspect_ratio)
                    else:
                        new_h = logo_height
                        new_w = int(logo_height * aspect_ratio)
                    pil_logo = pil_logo.resize((new_w, new_h), Image.LANCZOS)
                else:
                    # Aspect ratios are similar, safe to resize
                    pil_logo = pil_logo.resize((logo_width, logo_height), Image.LANCZOS)
            
            # Handle transparency properly
            if pil_logo.mode in ('RGBA', 'LA'):
                pil_image.paste(pil_logo, (placement_x, placement_y), pil_logo)
            else:
                pil_image.paste(pil_logo, (placement_x, placement_y))
            
            # Convert back to numpy array
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            print(f"Error creating composite: {e}")
            return image
    
    def parse_s3_url(self, s3_url):
        """Parse S3 URL to extract bucket and key"""
        try:
            parsed = urlparse(s3_url)
            # Handle s3://bucket/key format
            if parsed.scheme == 's3':
                bucket = parsed.netloc
                key = parsed.path.lstrip('/')
                return bucket, key
            # Handle https://bucket.s3.amazonaws.com/key format
            elif 's3.amazonaws.com' in parsed.netloc:
                bucket = parsed.netloc.split('.')[0]
                key = parsed.path.lstrip('/')
                return bucket, key
            else:
                return None, None
        except:
            return None, None
    
    def upload_to_s3(self, image_array, original_s3_url):
        """Upload composite image to S3 in same location as original"""
        try:
            bucket, original_key = self.parse_s3_url(original_s3_url)
            if not bucket or not original_key:
                return None
            
            # Create new key with -logo suffix
            key_parts = original_key.rsplit('.', 1)
            if len(key_parts) == 2:
                new_key = f"{key_parts[0]}-logo.{key_parts[1]}"
            else:
                new_key = f"{original_key}-logo.png"
            
            # Convert image array to bytes
            success, buffer = cv2.imencode('.png', image_array)
            if not success:
                return None
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=bucket,
                Key=new_key,
                Body=buffer.tobytes(),
                ContentType='image/png'
            )
            
            # Return the S3 URL
            return f"https://{bucket}.s3.amazonaws.com/{new_key}"
            
        except (NoCredentialsError, ClientError) as e:
            print(f"S3 upload error: {e}")
            return None
    
    def get_logo_dimensions(self, dark_logo_url, light_logo_url):
        """Get actual logo dimensions from one of the logo URLs"""
        try:
            # Try dark logo first
            logo_image = self.download_image(dark_logo_url)
            h, w = logo_image.shape[:2]
            return w, h
        except:
            try:
                # Fallback to light logo
                logo_image = self.download_image(light_logo_url)
                h, w = logo_image.shape[:2]
                return w, h
            except:
                # Ultimate fallback to default
                return 100, 50
    
    def analyze_placement(self, image_url, dark_logo_url, light_logo_url, return_image=True, upload_to_s3=True):
        """Main analysis function"""
        try:
            # Download and process image
            image = self.download_image(image_url)
            h, w = image.shape[:2]
            
            # Get actual logo dimensions
            logo_width, logo_height = self.get_logo_dimensions(dark_logo_url, light_logo_url)
            
            # Analyze all corners for detailed reporting
            corners = ['top-left', 'top-right', 'bottom-left', 'bottom-right']
            all_corner_results = []
            
            for corner in corners:
                corner_result = self.analyze_corner_space(image, corner, logo_width, logo_height)
                if corner_result:
                    # Add bias for corners (bottom-right most preferred)
                    if corner == 'bottom-right':
                        corner_result['suitability'] *= 1.25  # 25% bonus for bottom-right
                    elif corner == 'bottom-left':
                        corner_result['suitability'] *= 1.15  # 15% bonus for bottom-left
                    elif corner == 'top-right':
                        corner_result['suitability'] *= 1.05  # 5% bonus for top-right
                    
                    all_corner_results.append(corner_result)
            
            # Sort by suitability
            all_corner_results.sort(key=lambda x: x['suitability'], reverse=True)
            best_corner = all_corner_results[0] if all_corner_results else None
            
            # Base response structure (simplified)
            result = {
                'status': 'failed',
                'reason': None,
                'placement': None,
                'selected_logo': None,
                'output_image': None
            }
            
            if not best_corner:
                result['reason'] = 'No corners found suitable for logo placement'
                return result
            
            if not best_corner['space_sufficient']:
                result['reason'] = f"Insufficient space in best corner ({best_corner['corner']}). Available: {best_corner['available_width']}x{best_corner['available_height']}, Required: {logo_width}x{logo_height}"
                return result
            
            if best_corner['suitability'] < 0.3:  # Low confidence threshold
                result['reason'] = f"Low placement confidence ({best_corner['suitability']:.2f}) in best corner ({best_corner['corner']}). May have text or visual conflicts."
                return result
            
            # Success case
            result['status'] = 'successful'
            
            # Select logo variant
            logo_selection = self.select_logo_variant(
                image,
                best_corner['placement_x'],
                best_corner['placement_y'],
                logo_width,
                logo_height
            )
            
            selected_logo_url = dark_logo_url if logo_selection['use_dark_logo'] else light_logo_url
            
            # Update result with success data
            result.update({
                'placement': {
                    'corner': best_corner['corner'],
                    'x': best_corner['placement_x'],
                    'y': best_corner['placement_y'],
                    'width': logo_width,
                    'height': logo_height
                },
                'selected_logo': selected_logo_url
            })
            
            # Create composite image if requested
            if return_image:
                composite = self.create_logo_composite(
                    image, 
                    selected_logo_url,
                    best_corner['placement_x'],
                    best_corner['placement_y'],
                    logo_width, logo_height
                )
                
                # Handle S3 vs local storage based on preference
                if upload_to_s3:
                    s3_url = self.upload_to_s3(composite, image_url)
                    if s3_url:
                        result['output_image'] = s3_url
                    else:
                        # S3 failed, fallback to local file
                        output_filename = f"output_{uuid.uuid4().hex[:8]}.png"
                        output_path = os.path.join("outputs", output_filename)
                        os.makedirs("outputs", exist_ok=True)
                        cv2.imwrite(output_path, composite)
                        result['output_image'] = output_path
                else:
                    # Force local storage
                    output_filename = f"output_{uuid.uuid4().hex[:8]}.png"
                    output_path = os.path.join("outputs", output_filename)
                    os.makedirs("outputs", exist_ok=True)
                    cv2.imwrite(output_path, composite)
                    result['output_image'] = output_path
            
            return result
            
        except Exception as e:
            return {
                'status': 'failed',
                'reason': f'Processing error: {str(e)}',
                'placement': None,
                'selected_logo': None,
                'output_image': None
            }

analyzer = LogoPlacementAnalyzer()

@app.route('/analyze-placement', methods=['POST'])
def analyze_placement():
    """Analyze logo placement for given image and logo variants"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        required_fields = ['image_url', 'dark_logo_url', 'light_logo_url']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user wants the output image and S3 upload preference
        return_image = data.get('return_image', True)  # Default to True as promised
        upload_to_s3 = data.get('upload_to_s3', True)
        
        result = analyzer.analyze_placement(
            data['image_url'],
            data['dark_logo_url'],
            data['light_logo_url'],
            return_image,
            upload_to_s3
        )
        
        # Return appropriate HTTP status based on analysis result
        if result['status'] == 'successful':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'logo-placement-analyzer'})

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """Delete output files"""
    try:
        data = request.get_json()
        
        if not data or 'files' not in data:
            return jsonify({'error': 'No files specified'}), 400
        
        files = data['files']
        if not isinstance(files, list):
            files = [files]
        
        deleted = []
        errors = []
        
        for file_path in files:
            try:
                if os.path.exists(file_path) and file_path.startswith('outputs/'):
                    os.remove(file_path)
                    deleted.append(file_path)
                else:
                    errors.append(f"File not found or invalid path: {file_path}")
            except Exception as e:
                errors.append(f"Error deleting {file_path}: {str(e)}")
        
        return jsonify({
            'deleted': deleted,
            'errors': errors
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)