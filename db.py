"""
Database functions for the Lease Clause Classifier API.
Handles MongoDB operations for storing and retrieving classification results.
"""

import os
from datetime import datetime, timezone

from utils import log_success, log_error


def get_mongo_client(mongo_uri):
    """
    Create and return a MongoDB client.

    Args:
        mongo_uri: MongoDB connection URI.

    Returns:
        MongoClient instance or None if failed.
    """
    try:
        from pymongo import MongoClient
        return MongoClient(mongo_uri)
    except ImportError as e:
        log_error("pymongo library not installed", error=str(e))
        return None
    except Exception as e:
        log_error("Failed to create MongoDB client", error=str(e))
        return None


def save_to_mongodb(output, mongo_uri, mongo_db, mongo_collection):
    """
    Save output to MongoDB database.

    Args:
        output: Dictionary to save.
        mongo_uri: MongoDB connection URI.
        mongo_db: Database name.
        mongo_collection: Collection name.

    Returns:
        Inserted document ID as string or None if failed.
    """
    try:
        log_success("Saving to MongoDB", database=mongo_db, collection=mongo_collection)
        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[mongo_collection]

        output["created_at"] = datetime.now(timezone.utc)

        result = collection.insert_one(output)
        client.close()

        log_success("MongoDB save successful", document_id=str(result.inserted_id), database=mongo_db)
        return str(result.inserted_id)
    except ImportError as e:
        log_error("pymongo library not installed", error=str(e))
        return None
    except Exception as e:
        log_error("MongoDB save failed", database=mongo_db, collection=mongo_collection, error=str(e))
        return None


def get_mongo_config(config):
    """
    Extract MongoDB configuration from config dict.

    Args:
        config: Application configuration dictionary.

    Returns:
        Tuple of (mongo_uri, mongo_db, mongo_collection).
    """
    mongo_config = config.get("mongodb", {})
    mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
    mongo_db = mongo_config.get("database", "")
    mongo_collection = mongo_config.get("collection", "cube_outputs")
    return mongo_uri, mongo_db, mongo_collection


def find_document_by_id(collection, doc_id):
    """
    Find a document by ID, handling both ObjectId and string IDs.

    Args:
        collection: MongoDB collection.
        doc_id: Document ID (string).

    Returns:
        Document dict or None if not found.
    """
    from bson import ObjectId

    try:
        doc = collection.find_one({"_id": ObjectId(doc_id)})
    except Exception:
        doc = collection.find_one({"_id": doc_id})

    return doc


def update_document_by_id(collection, doc_id, update_data):
    """
    Update a document by ID, handling both ObjectId and string IDs.

    Args:
        collection: MongoDB collection.
        doc_id: Document ID (string).
        update_data: Dictionary of fields to update.

    Returns:
        True if successful, False otherwise.
    """
    from bson import ObjectId

    try:
        result = collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0 or result.matched_count > 0
    except Exception:
        try:
            result = collection.update_one(
                {"_id": doc_id},
                {"$set": update_data}
            )
            return result.modified_count > 0 or result.matched_count > 0
        except Exception:
            return False


def delete_document_by_id(collection, doc_id):
    """
    Delete a document by ID, handling both ObjectId and string IDs.

    Args:
        collection: MongoDB collection.
        doc_id: Document ID (string).

    Returns:
        Number of deleted documents (0 or 1).
    """
    from bson import ObjectId

    try:
        result = collection.delete_one({"_id": ObjectId(doc_id)})
        return result.deleted_count
    except Exception:
        result = collection.delete_one({"_id": doc_id})
        return result.deleted_count


def serialize_document(doc):
    """
    Serialize a MongoDB document for JSON response.

    Args:
        doc: MongoDB document dict.

    Returns:
        Serialized document dict.
    """
    if not doc:
        return doc

    # Convert ObjectId to string
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])

    # Convert datetime to ISO format string
    if 'created_at' in doc:
        doc['created_at'] = doc['created_at'].isoformat() if hasattr(doc['created_at'], 'isoformat') else str(doc['created_at'])

    return doc
