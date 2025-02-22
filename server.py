import os
from flask import Flask, redirect, jsonify, abort
from functools import lru_cache
import requests
from urllib.parse import urljoin

app = Flask(__name__)

# Configuration
GITHUB_USERNAME = "aizalovv"  # Replace with actual
GITHUB_REPO = "dialog-templates"
GITHUB_BRANCH = "main"
ALLOWED_DIALOG_TYPES = {'simpleDialog', 'iosDialog', 'customDialog'}

@lru_cache(maxsize=32)
def build_github_url(dialog_type: str) -> str:
    """Build GitHub URL with caching"""
    if dialog_type not in ALLOWED_DIALOG_TYPES:
        abort(404, description=f"Invalid dialog type: {dialog_type}")
    
    base_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/"
    return urljoin(base_url, f"{dialog_type}.zip")

@app.route('/<dialog_type>', methods=['GET'])
def serve_dialog(dialog_type: str):
    try:
        # Step 1: Get cached URL
        zip_url = build_github_url(dialog_type)
        
        # Step 2: Verify file exists
        response = requests.head(zip_url, timeout=5)
        if response.status_code != 200:
            abort(404, description="ZIP file not found on GitHub")
        
        # Step 3: Redirect
        return redirect(zip_url, code=302)
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f"GitHub connection error: {str(e)}")
        abort(503, description="Service unavailable")

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
