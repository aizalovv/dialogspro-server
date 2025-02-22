import os
from flask import Flask, redirect, jsonify, abort, request
from functools import lru_cache
import requests
from dotenv import load_dotenv
from urllib.parse import urljoin

load_dotenv()
app = Flask(__name__)

# Configuration
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'aizalovv')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'dialog-templates')
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'main')
ALLOWED_DIALOG_TYPES = {'simpleDialog', 'iosDialog', 'customDialog'}

# Cache with 1-hour timeout
@lru_cache(maxsize=128)
def get_github_zip_url(dialog_type: str) -> str:
    """Build GitHub raw URL with caching"""
    base_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/"
    return urljoin(base_url, f"{dialog_type}.zip")

@app.route('/<dialog_type>', methods=['GET'])
def serve_dialog(dialog_type: str):
    try:
        # Step 1: Validate dialog type
        if dialog_type not in ALLOWED_DIALOG_TYPES:
            abort(404, description=f"Invalid dialog type: {dialog_type}")
        
        # Step 2: Get cached URL
        zip_url = get_github_zip_url(dialog_type)
        
        # Step 3: Verify file exists
        head_resp = requests.head(zip_url)
        if head_resp.status_code != 200:
            abort(404, description="Template file not found on GitHub")
        
        # Step 4: Redirect to GitHub
        return redirect(zip_url, code=302)
    
    except requests.RequestException as e:
        app.logger.error(f"GitHub connection failed: {str(e)}")
        abort(503, description="Service temporarily unavailable")

# Error handlers remain same

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error="Internal server error"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
