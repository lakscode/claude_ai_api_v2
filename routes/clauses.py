"""
Clause management routes for the Lease Clause Classifier API.
Handles CRUD operations for clauses within documents.
Supports both new grouped format (clauses grouped by type with values array)
and old flat format (individual clauses with clause_index).
"""

import os

from flask import Blueprint, request, jsonify, current_app

from utils import log_success, log_error
from db import get_mongo_config, find_document_by_id, update_document_by_id

clauses_bp = Blueprint('clauses', __name__)


def is_grouped_format(clauses):
    """Check if clauses use the new grouped format (has 'values' array)."""
    if not clauses:
        return False
    return "values" in clauses[0]


def flatten_clauses(clauses):
    """Flatten grouped clauses into flat list for display."""
    flat_clauses = []
    for clause_group in clauses:
        if "values" in clause_group:
            clause_type = clause_group.get("type", "")
            clause_type_id = clause_group.get("type_id", "")
            for clause in clause_group.get("values", []):
                flat_clauses.append({
                    "clause_index": clause.get("clause_index", ""),
                    "text": clause.get("text", ""),
                    "type": clause_type,
                    "type_id": clause_type_id,
                    "confidence": clause.get("confidence", 0)
                })
        else:
            flat_clauses.append(clause_group)
    return flat_clauses


def find_clause_in_grouped(clauses, clause_index):
    """Find a clause by index in grouped format. Returns (group_index, value_index) or (None, None)."""
    for group_idx, clause_group in enumerate(clauses):
        if "values" in clause_group:
            for val_idx, clause in enumerate(clause_group.get("values", [])):
                if clause.get("clause_index") == clause_index:
                    return group_idx, val_idx
        else:
            if clause_group.get("clause_index") == clause_index:
                return group_idx, None
    return None, None


def reindex_clauses(clauses):
    """Reindex all clauses after deletion."""
    new_index = 0
    for clause_group in clauses:
        if "values" in clause_group:
            for clause in clause_group.get("values", []):
                clause["clause_index"] = new_index
                new_index += 1
        else:
            clause_group["clause_index"] = new_index
            new_index += 1
    return clauses


def count_total_clauses(clauses):
    """Count total individual clauses in grouped or flat format."""
    total = 0
    for clause_group in clauses:
        if "values" in clause_group:
            total += len(clause_group.get("values", []))
        else:
            total += 1
    return total


@clauses_bp.route('/data/<doc_id>/clauses', methods=['GET'])
def get_clauses(doc_id):
    """
    Get all clauses from a document.

    Path Parameters:
        - doc_id: MongoDB document ID

    Query Parameters:
        - flat: If 'true', returns clauses in flat format regardless of storage format

    Response:
        JSON with list of clauses.
    """
    try:
        log_success("Get clauses requested", endpoint=f"/data/{doc_id}/clauses", doc_id=doc_id)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/clauses")
            return jsonify({"error": "MongoDB not configured"}), 500

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)
        client.close()

        if not doc:
            log_error("Document not found", endpoint=f"/data/{doc_id}/clauses", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        clauses = doc.get("clauses", [])
        flat_param = request.args.get('flat', 'false').lower() == 'true'

        # Calculate totals
        if is_grouped_format(clauses):
            total_clauses = count_total_clauses(clauses)
            total_clause_types = len(clauses)
            if flat_param:
                clauses = flatten_clauses(clauses)
        else:
            total_clauses = len(clauses)
            total_clause_types = len(set(c.get("type", "") for c in clauses))

        log_success("Clauses retrieved", endpoint=f"/data/{doc_id}/clauses", doc_id=doc_id, total_clauses=total_clauses)

        return jsonify({
            "doc_id": doc_id,
            "pdf_file": doc.get("pdf_file"),
            "total_clauses": total_clauses,
            "total_clause_types": total_clause_types,
            "clauses": clauses
        }), 200

    except Exception as e:
        log_error("Failed to get clauses", endpoint=f"/data/{doc_id}/clauses", error=str(e))
        return jsonify({"error": str(e)}), 500


@clauses_bp.route('/data/<doc_id>/clauses/<int:clause_index>', methods=['GET'])
def get_clause(doc_id, clause_index):
    """
    Get a specific clause by index.

    Path Parameters:
        - doc_id: MongoDB document ID
        - clause_index: Index of the clause

    Response:
        JSON with clause data.
    """
    try:
        log_success("Get clause requested", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/clauses/{clause_index}")
            return jsonify({"error": "MongoDB not configured"}), 500

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)
        client.close()

        if not doc:
            log_error("Document not found", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        clauses = doc.get("clauses", [])

        if is_grouped_format(clauses):
            group_idx, val_idx = find_clause_in_grouped(clauses, clause_index)
            if group_idx is None:
                log_error("Clause not found", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
                return jsonify({"error": f"Clause with index {clause_index} not found"}), 404

            clause_group = clauses[group_idx]
            clause_data = clause_group["values"][val_idx]
            result = {
                "clause_index": clause_data.get("clause_index"),
                "text": clause_data.get("text"),
                "type": clause_group.get("type"),
                "type_id": clause_group.get("type_id"),
                "confidence": clause_data.get("confidence")
            }
        else:
            if clause_index < 0 or clause_index >= len(clauses):
                log_error("Clause index out of range", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
                return jsonify({"error": f"Clause index {clause_index} out of range"}), 404
            result = clauses[clause_index]

        log_success("Clause retrieved", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)

        return jsonify({
            "doc_id": doc_id,
            "clause": result
        }), 200

    except Exception as e:
        log_error("Failed to get clause", endpoint=f"/data/{doc_id}/clauses/{clause_index}", error=str(e))
        return jsonify({"error": str(e)}), 500


@clauses_bp.route('/data/<doc_id>/clauses/<int:clause_index>', methods=['PUT'])
def update_clause(doc_id, clause_index):
    """
    Update a specific clause in a document.

    Path Parameters:
        - doc_id: MongoDB document ID
        - clause_index: Index of the clause to update

    Request JSON:
        {
            "text": "Updated clause text",
            "type": "Updated clause type",
            "type_id": "Updated type ID",
            "confidence": 0.95
        }

    Response:
        JSON with updated clause.
    """
    try:
        log_success("Update clause requested", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id, clause_index=clause_index)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/clauses/{clause_index}")
            return jsonify({"error": "MongoDB not configured"}), 500

        data = request.get_json()
        if not data:
            log_error("Request body required", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
            return jsonify({"error": "Request body required"}), 400

        # Handle nested format: if data contains 'values' array, extract from it
        if "values" in data and isinstance(data["values"], list) and len(data["values"]) > 0:
            # Extract text and confidence from values[0]
            values_data = data["values"][0]
            if "text" in values_data:
                data["text"] = values_data["text"]
            if "confidence" in values_data:
                data["confidence"] = values_data["confidence"]

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)

        if not doc:
            client.close()
            log_error("Document not found", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        clauses = doc.get("clauses", [])

        if is_grouped_format(clauses):
            group_idx, val_idx = find_clause_in_grouped(clauses, clause_index)
            if group_idx is None:
                client.close()
                log_error("Clause not found", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
                return jsonify({"error": f"Clause with index {clause_index} not found"}), 404

            # Update clause data in the values array
            if "text" in data:
                clauses[group_idx]["values"][val_idx]["text"] = data["text"]
            if "confidence" in data:
                clauses[group_idx]["values"][val_idx]["confidence"] = data["confidence"]

            # Store current values before potential type change
            current_text = clauses[group_idx]["values"][val_idx].get("text", "")
            current_type = clauses[group_idx].get("type", "")
            current_confidence = clauses[group_idx]["values"][val_idx].get("confidence", 0)

            # If type is being changed, we need to move the clause to a different group
            if "type" in data and data["type"] != clauses[group_idx]["type"]:
                new_type = data["type"]
                new_type_id = data.get("type_id")

                # Remove from current group
                clause_data = clauses[group_idx]["values"].pop(val_idx)

                # Update text and confidence in the clause data
                if "text" in data:
                    clause_data["text"] = data["text"]
                if "confidence" in data:
                    clause_data["confidence"] = data["confidence"]

                # Remove empty groups
                if len(clauses[group_idx]["values"]) == 0:
                    clauses.pop(group_idx)

                # Find or create target group
                target_group_idx = None
                for idx, g in enumerate(clauses):
                    if g.get("type") == new_type:
                        target_group_idx = idx
                        break

                if target_group_idx is not None:
                    clauses[target_group_idx]["values"].append(clause_data)
                else:
                    # Create new group
                    clauses.append({
                        "type": new_type,
                        "type_id": new_type_id,
                        "values": [clause_data]
                    })

                updated_clause = {
                    "clause_index": clause_index,
                    "text": clause_data.get("text", ""),
                    "type": new_type,
                    "type_id": new_type_id,
                    "confidence": clause_data.get("confidence", 0)
                }
            else:
                updated_clause = {
                    "clause_index": clause_index,
                    "text": data.get("text", current_text),
                    "type": data.get("type", current_type),
                    "confidence": data.get("confidence", current_confidence)
                }
        else:
            # Old flat format
            if clause_index < 0 or clause_index >= len(clauses):
                client.close()
                log_error("Clause index out of range", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
                return jsonify({"error": f"Clause index {clause_index} out of range (0-{len(clauses)-1})"}), 400

            if "text" in data:
                clauses[clause_index]["text"] = data["text"]
            if "type" in data:
                clauses[clause_index]["type"] = data["type"]
            if "type_id" in data:
                clauses[clause_index]["type_id"] = data["type_id"]
            if "confidence" in data:
                clauses[clause_index]["confidence"] = data["confidence"]

            updated_clause = clauses[clause_index]

        # Update document
        update_document_by_id(collection, doc_id, {"clauses": clauses})
        client.close()

        log_success("Clause updated", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)

        return jsonify({
            "message": "Clause updated successfully",
            "doc_id": doc_id,
            "clause_index": clause_index,
            "clause": updated_clause
        }), 200

    except Exception as e:
        log_error("Failed to update clause", endpoint=f"/data/{doc_id}/clauses/{clause_index}", error=str(e))
        return jsonify({"error": str(e)}), 500


@clauses_bp.route('/data/<doc_id>/clauses/<int:clause_index>', methods=['DELETE'])
def delete_clause(doc_id, clause_index):
    """
    Delete a specific clause from a document.

    Path Parameters:
        - doc_id: MongoDB document ID
        - clause_index: Index of the clause to delete

    Response:
        JSON with deletion status.
    """
    try:
        log_success("Delete clause requested", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id, clause_index=clause_index)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/clauses/{clause_index}")
            return jsonify({"error": "MongoDB not configured"}), 500

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)

        if not doc:
            client.close()
            log_error("Document not found", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        clauses = doc.get("clauses", [])
        deleted_type = None

        if is_grouped_format(clauses):
            group_idx, val_idx = find_clause_in_grouped(clauses, clause_index)
            if group_idx is None:
                client.close()
                log_error("Clause not found", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
                return jsonify({"error": f"Clause with index {clause_index} not found"}), 404

            # Store deleted type before removing
            deleted_type = clauses[group_idx].get("type")

            # Remove clause from values array
            clauses[group_idx]["values"].pop(val_idx)

            # Remove empty groups
            if len(clauses[group_idx]["values"]) == 0:
                clauses.pop(group_idx)

            # Reindex remaining clauses
            clauses = reindex_clauses(clauses)
            total_clauses = count_total_clauses(clauses)
        else:
            # Old flat format
            if clause_index < 0 or clause_index >= len(clauses):
                client.close()
                log_error("Clause index out of range", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)
                return jsonify({"error": f"Clause index {clause_index} out of range (0-{len(clauses)-1})"}), 400

            deleted_clause = clauses.pop(clause_index)
            deleted_type = deleted_clause.get("type")

            # Reindex remaining clauses
            for i, clause in enumerate(clauses):
                clause["clause_index"] = i

            total_clauses = len(clauses)

        # Update document
        update_document_by_id(collection, doc_id, {
            "clauses": clauses,
            "total_clauses": total_clauses,
            "total_clause_types": len(clauses) if is_grouped_format(clauses) else len(set(c.get("type", "") for c in clauses))
        })
        client.close()

        log_success("Clause deleted", endpoint=f"/data/{doc_id}/clauses/{clause_index}", doc_id=doc_id)

        return jsonify({
            "message": "Clause deleted successfully",
            "doc_id": doc_id,
            "deleted_clause_index": clause_index,
            "deleted_clause_type": deleted_type,
            "remaining_clauses": total_clauses
        }), 200

    except Exception as e:
        log_error("Failed to delete clause", endpoint=f"/data/{doc_id}/clauses/{clause_index}", error=str(e))
        return jsonify({"error": str(e)}), 500


@clauses_bp.route('/data/<doc_id>/clauses', methods=['POST'])
def add_clause(doc_id):
    """
    Add a new clause to a document.

    Path Parameters:
        - doc_id: MongoDB document ID

    Request JSON:
        {
            "text": "New clause text",
            "type": "Clause type",
            "type_id": "Type ID",
            "confidence": 1.0
        }

    Response:
        JSON with added clause.
    """
    try:
        log_success("Add clause requested", endpoint=f"/data/{doc_id}/clauses", doc_id=doc_id)

        config = current_app.config.get('APP_CONFIG', {})
        mongo_uri, mongo_db, mongo_collection = get_mongo_config(config)

        if not mongo_uri or not mongo_db:
            log_error("MongoDB not configured", endpoint=f"/data/{doc_id}/clauses")
            return jsonify({"error": "MongoDB not configured"}), 500

        data = request.get_json()
        if not data or "text" not in data:
            log_error("Request body with 'text' field required", endpoint=f"/data/{doc_id}/clauses", doc_id=doc_id)
            return jsonify({"error": "Request body with 'text' field required"}), 400

        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        doc = find_document_by_id(collection, doc_id)

        if not doc:
            client.close()
            log_error("Document not found", endpoint=f"/data/{doc_id}/clauses", doc_id=doc_id)
            return jsonify({"error": "Document not found"}), 404

        clauses = doc.get("clauses", [])
        clause_type = data.get("type", "Unknown")
        clause_type_id = data.get("type_id")

        if is_grouped_format(clauses):
            # New grouped format
            # Calculate new clause index
            new_index = count_total_clauses(clauses)

            new_clause_data = {
                "clause_index": new_index,
                "text": data["text"],
                "confidence": data.get("confidence", 1.0)
            }

            # Find existing group or create new one
            target_group_idx = None
            for idx, g in enumerate(clauses):
                if g.get("type") == clause_type:
                    target_group_idx = idx
                    break

            if target_group_idx is not None:
                clauses[target_group_idx]["values"].append(new_clause_data)
            else:
                clauses.append({
                    "type": clause_type,
                    "type_id": clause_type_id,
                    "values": [new_clause_data]
                })

            total_clauses = count_total_clauses(clauses)
            new_clause = {
                "clause_index": new_index,
                "text": data["text"],
                "type": clause_type,
                "type_id": clause_type_id,
                "confidence": data.get("confidence", 1.0)
            }
        else:
            # Old flat format
            new_clause = {
                "clause_index": len(clauses),
                "text": data["text"],
                "type": clause_type,
                "type_id": clause_type_id,
                "confidence": data.get("confidence", 1.0)
            }
            clauses.append(new_clause)
            total_clauses = len(clauses)

        # Update document
        update_document_by_id(collection, doc_id, {
            "clauses": clauses,
            "total_clauses": total_clauses,
            "total_clause_types": len(clauses) if is_grouped_format(clauses) else len(set(c.get("type", "") for c in clauses))
        })
        client.close()

        log_success("Clause added", endpoint=f"/data/{doc_id}/clauses", doc_id=doc_id, clause_type=clause_type, total_clauses=total_clauses)

        return jsonify({
            "message": "Clause added successfully",
            "doc_id": doc_id,
            "clause": new_clause,
            "total_clauses": total_clauses
        }), 201

    except Exception as e:
        log_error("Failed to add clause", endpoint=f"/data/{doc_id}/clauses", error=str(e))
        return jsonify({"error": str(e)}), 500
