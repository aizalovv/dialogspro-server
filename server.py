import os
from flask import Flask, redirect, jsonify, abort
from functools import lru_cache
import requests
from dotenv import load_dotenv
from urllib.parse import urljoin

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'aizalovv')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'dialog-templates')
GITHUB_BRANCH = os.getenv('GITHUB_BRANCH', 'main')
ALLOWED_DIALOG_TYPES = {'simpleDialog', 'iosDialog', 'customDialog'}

# Cache GitHub API responses for 1 hour
@app.before_request
@lru_cache(maxsize=128)
def get_github_zip_url(dialog_type: str) -> str:
    """Validate dialog type and build GitHub raw URL"""
    if dialog_type not in ALLOWED_DIALOG_TYPES:
        abort(404, description="Dialog type not found")
    
    base_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/"
    return urljoin(base_url, f"{dialog_type}.zip")

@app.route('/<dialog_type>', methods=['GET'])
def serve_dialog(dialog_type: str):
    """Main endpoint to serve dialog ZIP files"""
    try:
        # Verify dialog type
        if dialog_type not in ALLOWED_DIALOG_TYPES:
            abort(404, description="Invalid dialog type")
        
        # Get GitHub URL
        zip_url = get_github_zip_url(dialog_type)
        
        # Verify file exists on GitHub
        head_resp = requests.head(zip_url)
        if head_resp.status_code != 200:
            abort(404, description="ZIP file not found on GitHub")
        
        # Redirect to GitHub raw URL
        return redirect(zip_url, code=302)
    
    except requests.RequestException as e:
        app.logger.error(f"GitHub connection error: {str(e)}")
        abort(502, description="Failed to connect to GitHub")

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error="Internal server error"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
