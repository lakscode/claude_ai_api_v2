"""
Field management routes for the Lease Clause Classifier API.
Handles CRUD operations for fields within documents.
"""

import os
import uuid as uuid_module

from flask import Blueprint, request, jsonify, current_app

from utils import log_success, log_error
from db import get_mongo_config, find_document_by_id, update_document_by_id

fields_bp = Blueprint('fields', __name__)


@fields_bp.route('/data/<doc_id>/fields', methods=['GET'])
def get_fields(doc_id):
    """
    Get all fields from a document.

    Path Parameters:
        - doc_id: MongoDB document ID

    Response:
        JSON with list of fields.
    """
    try:
        log_success("Get fields requested", endpoint=f"/data/{doc_id}/fields", doc_id=doc_id)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/fields")
            return jsonify({"error": "MongoDB not configured"}), 500

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)
        client.close()

        if not doc:
            log_error("Document not found", endpoint=f"/data/{doc_id}/fields", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        fields = doc.get("fields", [])

        log_success("Fields retrieved", endpoint=f"/data/{doc_id}/fields", doc_id=doc_id, total_fields=len(fields))

        return jsonify({
            "doc_id": doc_id,
            "pdf_file": doc.get("pdf_file"),
            "total_fields": len(fields),
            "fields": fields
        }), 200

    except Exception as e:
        log_error("Failed to get fields", endpoint=f"/data/{doc_id}/fields", error=str(e))
        return jsonify({"error": str(e)}), 500


@fields_bp.route('/data/<doc_id>/fields/<field_id>', methods=['GET'])
def get_field(doc_id, field_id):
    """
    Get a specific field by ID.

    Path Parameters:
        - doc_id: MongoDB document ID
        - field_id: Field ID

    Response:
        JSON with field data.
    """
    try:
        log_success("Get field requested", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id, field_id=field_id)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/fields/{field_id}")
            return jsonify({"error": "MongoDB not configured"}), 500

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)
        client.close()

        if not doc:
            log_error("Document not found", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        fields = doc.get("fields", [])

        # Find field by field_id
        target_field = None
        for field in fields:
            if field.get("field_id") == field_id:
                target_field = field
                break

        if target_field is None:
            log_error("Field not found", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id, field_id=field_id)
            return jsonify({"error": f"Field with ID '{field_id}' not found"}), 404

        log_success("Field retrieved", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id, field_name=target_field.get("field_name"))

        return jsonify({
            "doc_id": doc_id,
            "field": target_field
        }), 200

    except Exception as e:
        log_error("Failed to get field", endpoint=f"/data/{doc_id}/fields/{field_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@fields_bp.route('/data/<doc_id>/fields/<field_id>', methods=['PUT'])
def update_field(doc_id, field_id):
    """
    Update a specific field in a document.

    Path Parameters:
        - doc_id: MongoDB document ID
        - field_id: Field ID to update

    Request JSON:
        {
            "field_name": "Updated field name",
            "values": ["value1", "value2"],
            "clause_indices": [0, 1, 2]
        }

    Response:
        JSON with updated field.
    """
    try:
        log_success("Update field requested", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id, field_id=field_id)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/fields/{field_id}")
            return jsonify({"error": "MongoDB not configured"}), 500

        data = request.get_json()
        if not data:
            log_error("Request body required", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id)
            return jsonify({"error": "Request body required"}), 400

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)

        if not doc:
            client.close()
            log_error("Document not found", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        fields = doc.get("fields", [])

        # Find field by field_id
        field_index = None
        for i, field in enumerate(fields):
            if field.get("field_id") == field_id:
                field_index = i
                break

        if field_index is None:
            client.close()
            log_error("Field not found", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id, field_id=field_id)
            return jsonify({"error": f"Field with ID '{field_id}' not found"}), 404

        # Update field
        if "field_name" in data:
            fields[field_index]["field_name"] = data["field_name"]
        if "values" in data:
            fields[field_index]["values"] = data["values"]
        if "clause_indices" in data:
            fields[field_index]["clause_indices"] = data["clause_indices"]

        # Update document
        update_document_by_id(collection, doc_id, {"fields": fields})
        client.close()

        log_success("Field updated", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id)

        return jsonify({
            "message": "Field updated successfully",
            "doc_id": doc_id,
            "field_id": field_id,
            "field": fields[field_index]
        }), 200

    except Exception as e:
        log_error("Failed to update field", endpoint=f"/data/{doc_id}/fields/{field_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@fields_bp.route('/data/<doc_id>/fields/<field_id>', methods=['DELETE'])
def delete_field(doc_id, field_id):
    """
    Delete a specific field from a document.

    Path Parameters:
        - doc_id: MongoDB document ID
        - field_id: Field ID to delete

    Response:
        JSON with deletion status.
    """
    try:
        log_success("Delete field requested", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id, field_id=field_id)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/fields/{field_id}")
            return jsonify({"error": "MongoDB not configured"}), 500

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)

        if not doc:
            client.close()
            log_error("Document not found", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        fields = doc.get("fields", [])

        # Find and remove field
        field_index = None
        deleted_field = None
        for i, field in enumerate(fields):
            if field.get("field_id") == field_id:
                field_index = i
                deleted_field = field
                break

        if field_index is None:
            client.close()
            log_error("Field not found", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id, field_id=field_id)
            return jsonify({"error": f"Field with ID '{field_id}' not found"}), 404

        fields.pop(field_index)

        # Update document
        update_document_by_id(collection, doc_id, {"fields": fields, "total_fields": len(fields)})
        client.close()

        log_success("Field deleted", endpoint=f"/data/{doc_id}/fields/{field_id}", doc_id=doc_id)

        return jsonify({
            "message": "Field deleted successfully",
            "doc_id": doc_id,
            "deleted_field_id": field_id,
            "deleted_field_name": deleted_field.get("field_name"),
            "remaining_fields": len(fields)
        }), 200

    except Exception as e:
        log_error("Failed to delete field", endpoint=f"/data/{doc_id}/fields/{field_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@fields_bp.route('/data/<doc_id>/fields', methods=['POST'])
def add_field(doc_id):
    """
    Add a new field to a document.

    Path Parameters:
        - doc_id: MongoDB document ID

    Request JSON:
        {
            "field_id": "unique_field_id",
            "field_name": "Field Name",
            "values": ["value1", "value2"],
            "clause_indices": [0, 1]
        }

    Response:
        JSON with added field.
    """
    try:
        log_success("Add field requested", endpoint=f"/data/{doc_id}/fields", doc_id=doc_id)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/fields")
            return jsonify({"error": "MongoDB not configured"}), 500

        data = request.get_json()
        if not data or "field_name" not in data:
            log_error("Request body with 'field_name' required", endpoint=f"/data/{doc_id}/fields", doc_id=doc_id)
            return jsonify({"error": "Request body with 'field_name' required"}), 400

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)

        if not doc:
            client.close()
            log_error("Document not found", endpoint=f"/data/{doc_id}/fields", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        fields = doc.get("fields", [])

        # Create new field
        new_field = {
            "field_id": data.get("field_id", str(uuid_module.uuid4())),
            "field_name": data["field_name"],
            "values": data.get("values", []),
            "clause_indices": data.get("clause_indices", [])
        }

        # Check for duplicate field_id
        for field in fields:
            if field.get("field_id") == new_field["field_id"]:
                client.close()
                log_error("Duplicate field ID", endpoint=f"/data/{doc_id}/fields", doc_id=doc_id, field_id=new_field["field_id"])
                return jsonify({"error": f"Field with ID '{new_field['field_id']}' already exists"}), 400

        fields.append(new_field)

        # Update document
        update_document_by_id(collection, doc_id, {"fields": fields, "total_fields": len(fields)})
        client.close()

        log_success("Field added", endpoint=f"/data/{doc_id}/fields", doc_id=doc_id, field_name=new_field.get("field_name"), total_fields=len(fields))

        return jsonify({
            "message": "Field added successfully",
            "doc_id": doc_id,
            "field": new_field,
            "total_fields": len(fields)
        }), 201

    except Exception as e:
        log_error("Failed to add field", endpoint=f"/data/{doc_id}/fields", error=str(e))
        return jsonify({"error": str(e)}), 500
