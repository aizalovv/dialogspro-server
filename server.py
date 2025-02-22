import os
from flask import Flask, redirect, jsonify, abort
from functools import lru_cache
import requests
from urllib.parse import urljoin

app = Flask(__name__)

# Configuration
GITHUB_USERNAME = "aizalovv"  # Case-sensitive GitHub username
GITHUB_REPO = "dialogspro-server"           # Exact repository name
GITHUB_BRANCH = "main"                   # Branch name (usually main/master)
SUBFOLDER = "dialog-templates"           # Subfolder containing ZIPs
ALLOWED_DIALOG_TYPES = {'simpleDialog', 'iosDialog', 'customDialog'}

@lru_cache(maxsize=32)
def build_github_url(dialog_type: str) -> str:
    """Build GitHub URL with subfolder support"""
    if dialog_type not in ALLOWED_DIALOG_TYPES:
        abort(404, description=f"Invalid dialog type: {dialog_type}. Allowed types: {ALLOWED_DIALOG_TYPES}")
    
    base_url = (
        f"https://raw.githubusercontent.com/"
        f"{GITHUB_USERNAME}/{GITHUB_REPO}/"
        f"{GITHUB_BRANCH}/{SUBFOLDER}/"
    )
    return urljoin(base_url, f"{dialog_type}.zip")

@app.route('/<dialog_type>', methods=['GET'])
def serve_dialog(dialog_type: str):
    try:
        # Debugging: Print requested type
        print(f"[DEBUG] Requested dialog type: {dialog_type}")
        
        # Get GitHub URL
        zip_url = build_github_url(dialog_type)
        print(f"[DEBUG] Generated GitHub URL: {zip_url}")
        
        # Verify file existence
        response = requests.head(zip_url, timeout=10)
        print(f"[DEBUG] GitHub Response Code: {response.status_code}")
        
        if response.status_code != 200:
            abort(404, description=f"ZIP file not found at: {zip_url}")
        
        return redirect(zip_url, code=302)
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f"GitHub Connection Error: {str(e)}")
        abort(503, description="Temporary server issue. Please try later.")

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": error.description,
        "valid_types": list(ALLOWED_DIALOG_TYPES)
    }), 404

@app.errorhandler(503)
def service_unavailable(error):
    return jsonify({
        "error": error.description,
        "documentation": "https://your-api-docs.com"
    }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
