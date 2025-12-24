"""
Health and utility routes for the Lease Clause Classifier API.
"""

from flask import Blueprint, jsonify

from utils import log_success

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    log_success("Health check requested", endpoint="/health")
    return jsonify({"status": "healthy", "message": "Lease Classifier API is running"})


@health_bp.route('/models', methods=['GET'])
def list_models():
    """List available GPT models."""
    from flask import current_app

    config = current_app.config.get('APP_CONFIG', {})

    log_success("Models list requested", endpoint="/models")
    azure_config = config.get("azure_openai", config.get("azure", {}))
    models = azure_config.get("models", {})

    log_success("Models list retrieved", endpoint="/models", count=len(models))
    return jsonify({
        "default_model": config.get("openai", {}).get("gpt_model", "gpt-4o-mini"),
        "available_models": list(models.keys())
    })
