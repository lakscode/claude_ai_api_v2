"""
Swagger/OpenAPI documentation for the Lease Clause Classifier API.
"""

from flask_swagger_ui import get_swaggerui_blueprint

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Lease Clause Classifier API",
        'deepLinking': True,
        'displayRequestDuration': True,
        'docExpansion': 'list',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'tagsSorter': 'alpha',
        'operationsSorter': 'alpha'
    }
)

# OpenAPI 3.0 specification
swagger_spec = {
    "openapi": "3.0.3",
    "info": {
        "title": "Lease Clause Classifier API",
        "description": """
## Overview
The Lease Clause Classifier API provides endpoints for classifying lease document clauses using machine learning, extracting structured fields using OpenAI/Azure OpenAI, and managing classification data.

## Features
- **PDF Processing**: Upload and process PDF lease documents
- **Clause Classification**: Classify clauses using SVM classifier
- **Field Extraction**: Extract structured fields using OpenAI/Azure OpenAI
- **Data Management**: CRUD operations for clauses and fields
- **Export**: Export data as JSON, Excel, or PDF
- **Authentication**: Token-based authentication with role-based access control

## Authentication
Most endpoints require authentication via Bearer token. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Rate Limiting
API calls are not rate-limited by default, but OpenAI API calls are tracked.
        """,
        "version": "1.0.0",
        "contact": {
            "name": "API Support",
            "email": "support@example.com"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000",
            "description": "Development server"
        },
        {
            "url": "http://localhost:8080",
            "description": "Production server"
        }
    ],
    "tags": [
        {
            "name": "Health",
            "description": "Health check endpoints"
        },
        {
            "name": "Authentication",
            "description": "User authentication and session management"
        },
        {
            "name": "Users",
            "description": "User management (admin operations)"
        },
        {
            "name": "Classification",
            "description": "Clause classification endpoints"
        },
        {
            "name": "Data",
            "description": "Data retrieval and management"
        },
        {
            "name": "Clauses",
            "description": "Clause CRUD operations"
        },
        {
            "name": "Fields",
            "description": "Field CRUD operations"
        },
        {
            "name": "Export",
            "description": "Data export endpoints"
        },
        {
            "name": "Lease Uploads",
            "description": "Lease upload and batch processing endpoints"
        }
    ],
    "paths": {
        # Health endpoints
        "/health": {
            "get": {
                "tags": ["Health"],
                "summary": "Health check",
                "description": "Check if the API is running and healthy",
                "operationId": "healthCheck",
                "responses": {
                    "200": {
                        "description": "API is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HealthResponse"
                                },
                                "example": {
                                    "status": "healthy",
                                    "service": "lease-classifier-api",
                                    "version": "1.0.0",
                                    "classifier_loaded": True,
                                    "clause_types_count": 25
                                }
                            }
                        }
                    }
                }
            }
        },
        "/health/detailed": {
            "get": {
                "tags": ["Health"],
                "summary": "Detailed health check",
                "description": "Get detailed health information including MongoDB and OpenAI status",
                "operationId": "detailedHealthCheck",
                "responses": {
                    "200": {
                        "description": "Detailed health information",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DetailedHealthResponse"
                                }
                            }
                        }
                    }
                }
            }
        },

        # Authentication endpoints
        "/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "User login",
                "description": "Authenticate user and create a session token",
                "operationId": "login",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/LoginRequest"
                            },
                            "example": {
                                "username": "admin",
                                "password": "admin123"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Login successful",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/LoginResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Missing credentials",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Invalid credentials",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/auth/logout": {
            "post": {
                "tags": ["Authentication"],
                "summary": "User logout",
                "description": "Logout user and invalidate session token",
                "operationId": "logout",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Logout successful",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/MessageResponse"
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/auth/me": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Get current user",
                "description": "Get information about the currently authenticated user",
                "operationId": "getCurrentUser",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Current user info",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserResponse"
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/auth/validate": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Validate token",
                "description": "Validate a session token",
                "operationId": "validateToken",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Token validation result",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/TokenValidationResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/auth/refresh": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Refresh token",
                "description": "Refresh session token (get a new token)",
                "operationId": "refreshToken",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Token refreshed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/LoginResponse"
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },

        # Users endpoints
        "/users": {
            "get": {
                "tags": ["Users"],
                "summary": "Get all users",
                "description": "Get list of all users with optional filtering",
                "operationId": "getUsers",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "role",
                        "in": "query",
                        "description": "Filter by role",
                        "schema": {
                            "type": "string",
                            "enum": ["admin", "user", "editor", "viewer"]
                        }
                    },
                    {
                        "name": "is_active",
                        "in": "query",
                        "description": "Filter by active status",
                        "schema": {
                            "type": "boolean"
                        }
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum number of users to return",
                        "schema": {
                            "type": "integer",
                            "default": 100,
                            "maximum": 1000
                        }
                    },
                    {
                        "name": "skip",
                        "in": "query",
                        "description": "Number of users to skip",
                        "schema": {
                            "type": "integer",
                            "default": 0
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of users",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UsersListResponse"
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Users"],
                "summary": "Create user",
                "description": "Create a new user (admin only)",
                "operationId": "createUser",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/CreateUserRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "User created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Not authenticated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "403": {
                        "description": "Not authorized (admin only)",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/users/{user_id}": {
            "get": {
                "tags": ["Users"],
                "summary": "Get user by ID",
                "description": "Get a specific user by their ID",
                "operationId": "getUserById",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "path",
                        "required": True,
                        "description": "User ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "User info",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "User not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "put": {
                "tags": ["Users"],
                "summary": "Update user",
                "description": "Update a user (admin only)",
                "operationId": "updateUser",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "path",
                        "required": True,
                        "description": "User ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/UpdateUserRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "User updated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserResponse"
                                }
                            }
                        }
                    },
                    "403": {
                        "description": "Not authorized",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "User not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "delete": {
                "tags": ["Users"],
                "summary": "Delete user",
                "description": "Delete a user (admin only)",
                "operationId": "deleteUser",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "user_id",
                        "in": "path",
                        "required": True,
                        "description": "User ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "User deleted",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DeleteUserResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Cannot delete own account",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "403": {
                        "description": "Not authorized",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "User not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/users/search": {
            "get": {
                "tags": ["Users"],
                "summary": "Search users",
                "description": "Search users by username, email, or name",
                "operationId": "searchUsers",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "q",
                        "in": "query",
                        "required": True,
                        "description": "Search query",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum results",
                        "schema": {
                            "type": "integer",
                            "default": 100
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Search results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserSearchResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Search query required",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/users/stats": {
            "get": {
                "tags": ["Users"],
                "summary": "Get user statistics",
                "description": "Get statistics about users",
                "operationId": "getUserStats",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "User statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserStatsResponse"
                                }
                            }
                        }
                    }
                }
            }
        },

        # Classification endpoints
        "/classify": {
            "post": {
                "tags": ["Classification"],
                "summary": "Classify text",
                "description": "Classify a single clause text",
                "operationId": "classifyText",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ClassifyTextRequest"
                            },
                            "example": {
                                "text": "The Tenant shall pay rent on the first day of each month."
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Classification result",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ClassifyTextResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Text is required",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/classify/batch": {
            "post": {
                "tags": ["Classification"],
                "summary": "Classify multiple texts",
                "description": "Classify multiple clause texts in a single request",
                "operationId": "classifyBatch",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ClassifyBatchRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Batch classification results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ClassifyBatchResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/classify/pdf": {
            "post": {
                "tags": ["Classification"],
                "summary": "Process PDF",
                "description": "Upload and process a PDF file for clause classification and field extraction",
                "operationId": "classifyPdf",
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "required": ["file"],
                                "properties": {
                                    "file": {
                                        "type": "string",
                                        "format": "binary",
                                        "description": "PDF file to process"
                                    },
                                    "extract_fields": {
                                        "type": "boolean",
                                        "default": True,
                                        "description": "Whether to extract fields using OpenAI"
                                    },
                                    "save_to_db": {
                                        "type": "boolean",
                                        "default": True,
                                        "description": "Whether to save results to MongoDB"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "PDF processing result",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/PdfProcessingResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "No file provided or invalid file type",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/classify/types": {
            "get": {
                "tags": ["Classification"],
                "summary": "Get clause types",
                "description": "Get all available clause types supported by the classifier",
                "operationId": "getClauseTypes",
                "responses": {
                    "200": {
                        "description": "List of clause types",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ClauseTypesResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/classify/fields": {
            "get": {
                "tags": ["Classification"],
                "summary": "Get field definitions",
                "description": "Get all field definitions for field extraction",
                "operationId": "getFieldDefinitions",
                "responses": {
                    "200": {
                        "description": "List of field definitions",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/FieldDefinitionsResponse"
                                }
                            }
                        }
                    }
                }
            }
        },

        # Data endpoints
        "/data": {
            "get": {
                "tags": ["Data"],
                "summary": "Get all documents",
                "description": "Retrieve classification data from MongoDB with pagination",
                "operationId": "getAllDocuments",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum number of documents",
                        "schema": {
                            "type": "integer",
                            "default": 100,
                            "maximum": 1000
                        }
                    },
                    {
                        "name": "skip",
                        "in": "query",
                        "description": "Number of documents to skip",
                        "schema": {
                            "type": "integer",
                            "default": 0
                        }
                    },
                    {
                        "name": "sort_by",
                        "in": "query",
                        "description": "Field to sort by",
                        "schema": {
                            "type": "string",
                            "default": "created_at"
                        }
                    },
                    {
                        "name": "sort_order",
                        "in": "query",
                        "description": "Sort order",
                        "schema": {
                            "type": "string",
                            "enum": ["asc", "desc"],
                            "default": "desc"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of documents",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DocumentsListResponse"
                                }
                            }
                        }
                    },
                    "500": {
                        "description": "MongoDB not configured",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/data/{doc_id}": {
            "get": {
                "tags": ["Data"],
                "summary": "Get document by ID",
                "description": "Get a specific document by its MongoDB ID",
                "operationId": "getDocumentById",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Document data",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DocumentResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "delete": {
                "tags": ["Data"],
                "summary": "Delete document",
                "description": "Delete a document by its MongoDB ID",
                "operationId": "deleteDocument",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Document deleted",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DeleteDocumentResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/data/search": {
            "get": {
                "tags": ["Data"],
                "summary": "Search documents",
                "description": "Search documents by PDF filename or clause content",
                "operationId": "searchDocuments",
                "parameters": [
                    {
                        "name": "q",
                        "in": "query",
                        "required": True,
                        "description": "Search query",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum results",
                        "schema": {
                            "type": "integer",
                            "default": 100
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Search results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DocumentSearchResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/data/stats": {
            "get": {
                "tags": ["Data"],
                "summary": "Get statistics",
                "description": "Get overall statistics about stored documents",
                "operationId": "getDataStats",
                "responses": {
                    "200": {
                        "description": "Data statistics",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DataStatsResponse"
                                }
                            }
                        }
                    }
                }
            }
        },

        # Clauses endpoints
        "/data/{doc_id}/clauses": {
            "get": {
                "tags": ["Clauses"],
                "summary": "Get all clauses",
                "description": "Get all clauses from a document",
                "operationId": "getClauses",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "flat",
                        "in": "query",
                        "description": "Return clauses in flat format instead of grouped",
                        "schema": {
                            "type": "boolean",
                            "default": False
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of clauses",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ClausesResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Clauses"],
                "summary": "Add clause",
                "description": "Add a new clause to a document",
                "operationId": "addClause",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/AddClauseRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Clause added",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ClauseResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/data/{doc_id}/clauses/{clause_index}": {
            "get": {
                "tags": ["Clauses"],
                "summary": "Get clause by index",
                "description": "Get a specific clause by its index",
                "operationId": "getClauseByIndex",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "clause_index",
                        "in": "path",
                        "required": True,
                        "description": "Clause index",
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Clause data",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/SingleClauseResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document or clause not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "put": {
                "tags": ["Clauses"],
                "summary": "Update clause",
                "description": "Update a specific clause",
                "operationId": "updateClause",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "clause_index",
                        "in": "path",
                        "required": True,
                        "description": "Clause index",
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/UpdateClauseRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Clause updated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ClauseResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document or clause not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "delete": {
                "tags": ["Clauses"],
                "summary": "Delete clause",
                "description": "Delete a specific clause",
                "operationId": "deleteClause",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "clause_index",
                        "in": "path",
                        "required": True,
                        "description": "Clause index",
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Clause deleted",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DeleteClauseResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document or clause not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },

        # Fields endpoints
        "/data/{doc_id}/fields": {
            "get": {
                "tags": ["Fields"],
                "summary": "Get all fields",
                "description": "Get all fields from a document",
                "operationId": "getFields",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of fields",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/FieldsResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Fields"],
                "summary": "Add field",
                "description": "Add a new field to a document",
                "operationId": "addField",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/AddFieldRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Field added",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/FieldResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/data/{doc_id}/fields/{field_id}": {
            "get": {
                "tags": ["Fields"],
                "summary": "Get field by ID",
                "description": "Get a specific field by its ID",
                "operationId": "getFieldById",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "field_id",
                        "in": "path",
                        "required": True,
                        "description": "Field ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Field data",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/SingleFieldResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document or field not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "put": {
                "tags": ["Fields"],
                "summary": "Update field",
                "description": "Update a specific field",
                "operationId": "updateField",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "field_id",
                        "in": "path",
                        "required": True,
                        "description": "Field ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/UpdateFieldRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Field updated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/FieldResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document or field not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "delete": {
                "tags": ["Fields"],
                "summary": "Delete field",
                "description": "Delete a specific field",
                "operationId": "deleteField",
                "parameters": [
                    {
                        "name": "doc_id",
                        "in": "path",
                        "required": True,
                        "description": "MongoDB document ID",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "field_id",
                        "in": "path",
                        "required": True,
                        "description": "Field ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Field deleted",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DeleteFieldResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document or field not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },

        # Export endpoints
        "/data/export/json": {
            "get": {
                "tags": ["Export"],
                "summary": "Export as JSON",
                "description": "Export classification data as JSON file",
                "operationId": "exportJson",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum records to export",
                        "schema": {
                            "type": "integer",
                            "default": 1000,
                            "maximum": 10000
                        }
                    },
                    {
                        "name": "doc_id",
                        "in": "query",
                        "description": "Export specific document by ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "JSON file download",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "string",
                                    "format": "binary"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/data/export/excel": {
            "get": {
                "tags": ["Export"],
                "summary": "Export as Excel",
                "description": "Export classification data as Excel file",
                "operationId": "exportExcel",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum records to export",
                        "schema": {
                            "type": "integer",
                            "default": 1000,
                            "maximum": 10000
                        }
                    },
                    {
                        "name": "doc_id",
                        "in": "query",
                        "description": "Export specific document by ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Excel file download",
                        "content": {
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                                "schema": {
                                    "type": "string",
                                    "format": "binary"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/data/export/pdf": {
            "get": {
                "tags": ["Export"],
                "summary": "Export as PDF",
                "description": "Export classification data as PDF file",
                "operationId": "exportPdf",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Maximum records to export",
                        "schema": {
                            "type": "integer",
                            "default": 100,
                            "maximum": 1000
                        }
                    },
                    {
                        "name": "doc_id",
                        "in": "query",
                        "description": "Export specific document by ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "PDF file download",
                        "content": {
                            "application/pdf": {
                                "schema": {
                                    "type": "string",
                                    "format": "binary"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Document not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },

        # Lease Upload endpoints
        "/leases/upload": {
            "post": {
                "tags": ["Lease Uploads"],
                "summary": "Upload a lease PDF",
                "description": "Upload a single lease PDF to storage and save metadata in the lease_uploads collection with pending status",
                "operationId": "uploadLease",
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "required": ["pdf"],
                                "properties": {
                                    "pdf": {
                                        "type": "string",
                                        "format": "binary",
                                        "description": "PDF file to upload"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Lease uploaded successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/LeaseUploadResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request (no file or invalid file type)",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "500": {
                        "description": "Upload failed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/leases/upload/batch": {
            "post": {
                "tags": ["Lease Uploads"],
                "summary": "Upload multiple lease PDFs",
                "description": "Upload multiple lease PDFs at once. Each file is saved with pending status.",
                "operationId": "uploadLeasesBatch",
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "required": ["pdf"],
                                "properties": {
                                    "pdf": {
                                        "type": "array",
                                        "items": {
                                            "type": "string",
                                            "format": "binary"
                                        },
                                        "description": "Multiple PDF files to upload"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Batch upload completed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/LeaseBatchUploadResponse"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "No files provided",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/leases": {
            "get": {
                "tags": ["Lease Uploads"],
                "summary": "Get all uploaded leases",
                "description": "Get all uploaded leases with optional filtering by status and pagination",
                "operationId": "getLeases",
                "parameters": [
                    {
                        "name": "status",
                        "in": "query",
                        "description": "Filter by status",
                        "schema": {
                            "type": "string",
                            "enum": ["pending", "processing", "processed", "failed"]
                        }
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "description": "Page number",
                        "schema": {
                            "type": "integer",
                            "default": 1
                        }
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Items per page",
                        "schema": {
                            "type": "integer",
                            "default": 20,
                            "maximum": 100
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of leases",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/LeasesListResponse"
                                }
                            }
                        }
                    },
                    "500": {
                        "description": "Database not configured",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/leases/{lease_id}": {
            "get": {
                "tags": ["Lease Uploads"],
                "summary": "Get lease by ID",
                "description": "Get a specific uploaded lease by its ID",
                "operationId": "getLeaseById",
                "parameters": [
                    {
                        "name": "lease_id",
                        "in": "path",
                        "required": True,
                        "description": "Lease ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Lease details",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/LeaseDocument"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Lease not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            },
            "delete": {
                "tags": ["Lease Uploads"],
                "summary": "Delete a lease",
                "description": "Delete an uploaded lease record",
                "operationId": "deleteLease",
                "parameters": [
                    {
                        "name": "lease_id",
                        "in": "path",
                        "required": True,
                        "description": "Lease ID",
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Lease deleted",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/MessageResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Lease not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/leases/process": {
            "post": {
                "tags": ["Lease Uploads"],
                "summary": "Trigger batch processing",
                "description": "Trigger batch processing of pending leases. Processes 2 files at a time, updates status to 'processing', then 'processed' on completion. Runs in background.",
                "operationId": "triggerLeaseProcessing",
                "responses": {
                    "202": {
                        "description": "Processing started",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ProcessingStartResponse"
                                }
                            }
                        }
                    },
                    "200": {
                        "description": "Processing already in progress or no pending leases",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ProcessingStatusResponse"
                                }
                            }
                        }
                    },
                    "500": {
                        "description": "Database not configured",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/leases/process/status": {
            "get": {
                "tags": ["Lease Uploads"],
                "summary": "Get processing status",
                "description": "Get the current processing status and counts by status",
                "operationId": "getProcessingStatus",
                "responses": {
                    "200": {
                        "description": "Processing status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ProcessingStatusResponse"
                                }
                            }
                        }
                    },
                    "500": {
                        "description": "Database not configured",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/leases/import-from-folders": {
            "post": {
                "tags": ["Lease Uploads"],
                "summary": "Import PDFs from input folders",
                "description": "Import PDF files from folders placed inside the input_folders directory. Scans all subfolders recursively and uploads any PDF files found.",
                "operationId": "importFromFolders",
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ImportFromFoldersRequest"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Import completed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ImportFromFoldersResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Input folders directory not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "500": {
                        "description": "Database not configured or import failed",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/leases/folders": {
            "get": {
                "tags": ["Lease Uploads"],
                "summary": "List input folders",
                "description": "List all folders inside the input_folders directory with PDF file counts",
                "operationId": "listInputFolders",
                "parameters": [
                    {
                        "name": "input_path",
                        "in": "query",
                        "description": "Custom path to input_folders directory",
                        "schema": {
                            "type": "string",
                            "default": "input_folders"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of folders",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ListFoldersResponse"
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Input folders directory not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your bearer token"
            }
        },
        "schemas": {
            # Common schemas
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "Error message"
                    }
                }
            },
            "MessageResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Success message"
                    }
                }
            },

            # Health schemas
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["healthy", "unhealthy"]
                    },
                    "service": {
                        "type": "string"
                    },
                    "version": {
                        "type": "string"
                    },
                    "classifier_loaded": {
                        "type": "boolean"
                    },
                    "clause_types_count": {
                        "type": "integer"
                    }
                }
            },
            "DetailedHealthResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string"
                    },
                    "service": {
                        "type": "string"
                    },
                    "version": {
                        "type": "string"
                    },
                    "classifier_loaded": {
                        "type": "boolean"
                    },
                    "clause_types_count": {
                        "type": "integer"
                    },
                    "mongodb_connected": {
                        "type": "boolean"
                    },
                    "openai_configured": {
                        "type": "boolean"
                    },
                    "uptime_seconds": {
                        "type": "number"
                    }
                }
            },

            # Auth schemas
            "LoginRequest": {
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username or email"
                    },
                    "password": {
                        "type": "string",
                        "format": "password",
                        "description": "User password"
                    }
                }
            },
            "LoginResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "token": {
                        "type": "string",
                        "description": "Bearer token"
                    },
                    "token_type": {
                        "type": "string",
                        "enum": ["Bearer"]
                    },
                    "user": {
                        "$ref": "#/components/schemas/User"
                    }
                }
            },
            "TokenValidationResponse": {
                "type": "object",
                "properties": {
                    "valid": {
                        "type": "boolean"
                    },
                    "session": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string"
                            },
                            "username": {
                                "type": "string"
                            },
                            "role": {
                                "type": "string"
                            },
                            "expires_at": {
                                "type": "string",
                                "format": "date-time"
                            }
                        }
                    },
                    "user": {
                        "$ref": "#/components/schemas/User"
                    },
                    "error": {
                        "type": "string"
                    }
                }
            },

            # User schemas
            "User": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string"
                    },
                    "username": {
                        "type": "string"
                    },
                    "email": {
                        "type": "string",
                        "format": "email"
                    },
                    "first_name": {
                        "type": "string"
                    },
                    "last_name": {
                        "type": "string"
                    },
                    "role": {
                        "type": "string",
                        "enum": ["admin", "user", "editor", "viewer"]
                    },
                    "is_active": {
                        "type": "boolean"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "last_login": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": True
                    }
                }
            },
            "UserResponse": {
                "type": "object",
                "properties": {
                    "user": {
                        "$ref": "#/components/schemas/User"
                    },
                    "message": {
                        "type": "string"
                    }
                }
            },
            "UsersListResponse": {
                "type": "object",
                "properties": {
                    "total": {
                        "type": "integer"
                    },
                    "limit": {
                        "type": "integer"
                    },
                    "skip": {
                        "type": "integer"
                    },
                    "count": {
                        "type": "integer"
                    },
                    "users": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/User"
                        }
                    }
                }
            },
            "CreateUserRequest": {
                "type": "object",
                "required": ["username", "email", "password"],
                "properties": {
                    "username": {
                        "type": "string"
                    },
                    "email": {
                        "type": "string",
                        "format": "email"
                    },
                    "password": {
                        "type": "string",
                        "format": "password"
                    },
                    "first_name": {
                        "type": "string"
                    },
                    "last_name": {
                        "type": "string"
                    },
                    "role": {
                        "type": "string",
                        "enum": ["admin", "user", "editor", "viewer"],
                        "default": "user"
                    }
                }
            },
            "UpdateUserRequest": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email"
                    },
                    "first_name": {
                        "type": "string"
                    },
                    "last_name": {
                        "type": "string"
                    },
                    "role": {
                        "type": "string",
                        "enum": ["admin", "user", "editor", "viewer"]
                    },
                    "is_active": {
                        "type": "boolean"
                    },
                    "password": {
                        "type": "string",
                        "format": "password"
                    }
                }
            },
            "DeleteUserResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "deleted_user_id": {
                        "type": "string"
                    },
                    "deleted_username": {
                        "type": "string"
                    }
                }
            },
            "UserSearchResponse": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    },
                    "count": {
                        "type": "integer"
                    },
                    "users": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/User"
                        }
                    }
                }
            },
            "UserStatsResponse": {
                "type": "object",
                "properties": {
                    "total_users": {
                        "type": "integer"
                    },
                    "active_users": {
                        "type": "integer"
                    },
                    "inactive_users": {
                        "type": "integer"
                    },
                    "users_by_role": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "integer"
                        }
                    }
                }
            },

            # Classification schemas
            "ClassifyTextRequest": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Clause text to classify"
                    }
                }
            },
            "ClassifyTextResponse": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string"
                    },
                    "predicted_type": {
                        "type": "string"
                    },
                    "type_id": {
                        "type": "string",
                        "nullable": True
                    },
                    "confidence": {
                        "type": "number",
                        "format": "float"
                    },
                    "all_probabilities": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "number"
                        }
                    }
                }
            },
            "ClassifyBatchRequest": {
                "type": "object",
                "required": ["texts"],
                "properties": {
                    "texts": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of clause texts to classify"
                    }
                }
            },
            "ClassifyBatchResponse": {
                "type": "object",
                "properties": {
                    "total_processed": {
                        "type": "integer"
                    },
                    "results": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/ClassifyTextResponse"
                        }
                    }
                }
            },
            "PdfProcessingResponse": {
                "type": "object",
                "properties": {
                    "pdf_file": {
                        "type": "string"
                    },
                    "total_clauses": {
                        "type": "integer"
                    },
                    "total_clause_types": {
                        "type": "integer"
                    },
                    "total_fields": {
                        "type": "integer"
                    },
                    "openai_api_calls": {
                        "type": "integer"
                    },
                    "field_extraction_enabled": {
                        "type": "boolean"
                    },
                    "clauses": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/ClauseGroup"
                        }
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/Field"
                        }
                    },
                    "_id": {
                        "type": "string",
                        "description": "MongoDB document ID (if saved)"
                    }
                }
            },
            "ClauseTypesResponse": {
                "type": "object",
                "properties": {
                    "total_types": {
                        "type": "integer"
                    },
                    "types": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string"
                                },
                                "id": {
                                    "type": "string",
                                    "nullable": True
                                }
                            }
                        }
                    }
                }
            },
            "FieldDefinitionsResponse": {
                "type": "object",
                "properties": {
                    "total_fields": {
                        "type": "integer"
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field_id": {
                                    "type": "string"
                                },
                                "field_name": {
                                    "type": "string"
                                },
                                "description": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                }
            },

            # Document/Data schemas
            "Document": {
                "type": "object",
                "properties": {
                    "_id": {
                        "type": "string"
                    },
                    "pdf_file": {
                        "type": "string"
                    },
                    "total_clauses": {
                        "type": "integer"
                    },
                    "total_clause_types": {
                        "type": "integer"
                    },
                    "total_fields": {
                        "type": "integer"
                    },
                    "openai_api_calls": {
                        "type": "integer"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "clauses": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/ClauseGroup"
                        }
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/Field"
                        }
                    }
                }
            },
            "DocumentResponse": {
                "type": "object",
                "properties": {
                    "document": {
                        "$ref": "#/components/schemas/Document"
                    }
                }
            },
            "DocumentsListResponse": {
                "type": "object",
                "properties": {
                    "total": {
                        "type": "integer"
                    },
                    "limit": {
                        "type": "integer"
                    },
                    "skip": {
                        "type": "integer"
                    },
                    "count": {
                        "type": "integer"
                    },
                    "documents": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/Document"
                        }
                    }
                }
            },
            "DocumentSearchResponse": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    },
                    "count": {
                        "type": "integer"
                    },
                    "documents": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/Document"
                        }
                    }
                }
            },
            "DeleteDocumentResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "deleted_id": {
                        "type": "string"
                    }
                }
            },
            "DataStatsResponse": {
                "type": "object",
                "properties": {
                    "total_documents": {
                        "type": "integer"
                    },
                    "total_clauses": {
                        "type": "integer"
                    },
                    "total_fields": {
                        "type": "integer"
                    },
                    "total_openai_calls": {
                        "type": "integer"
                    },
                    "clause_types_distribution": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "integer"
                        }
                    }
                }
            },

            # Clause schemas
            "ClauseGroup": {
                "type": "object",
                "description": "Grouped clauses by type",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Clause type name"
                    },
                    "type_id": {
                        "type": "string",
                        "nullable": True,
                        "description": "Clause type ID from mapping"
                    },
                    "values": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/ClauseValue"
                        }
                    }
                }
            },
            "ClauseValue": {
                "type": "object",
                "description": "Individual clause within a group",
                "properties": {
                    "clause_index": {
                        "type": "integer"
                    },
                    "text": {
                        "type": "string"
                    },
                    "confidence": {
                        "type": "number",
                        "format": "float"
                    }
                }
            },
            "Clause": {
                "type": "object",
                "description": "Flat clause representation",
                "properties": {
                    "clause_index": {
                        "type": "integer"
                    },
                    "text": {
                        "type": "string"
                    },
                    "type": {
                        "type": "string"
                    },
                    "type_id": {
                        "type": "string",
                        "nullable": True
                    },
                    "confidence": {
                        "type": "number",
                        "format": "float"
                    }
                }
            },
            "ClausesResponse": {
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string"
                    },
                    "pdf_file": {
                        "type": "string"
                    },
                    "total_clauses": {
                        "type": "integer"
                    },
                    "total_clause_types": {
                        "type": "integer"
                    },
                    "clauses": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/ClauseGroup"
                        }
                    }
                }
            },
            "SingleClauseResponse": {
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string"
                    },
                    "clause": {
                        "$ref": "#/components/schemas/Clause"
                    }
                }
            },
            "ClauseResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "doc_id": {
                        "type": "string"
                    },
                    "clause_index": {
                        "type": "integer"
                    },
                    "clause": {
                        "$ref": "#/components/schemas/Clause"
                    },
                    "total_clauses": {
                        "type": "integer"
                    }
                }
            },
            "AddClauseRequest": {
                "type": "object",
                "required": ["text"],
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Clause text"
                    },
                    "type": {
                        "type": "string",
                        "description": "Clause type",
                        "default": "Unknown"
                    },
                    "type_id": {
                        "type": "string",
                        "description": "Clause type ID"
                    },
                    "confidence": {
                        "type": "number",
                        "format": "float",
                        "default": 1.0
                    }
                }
            },
            "UpdateClauseRequest": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string"
                    },
                    "type": {
                        "type": "string"
                    },
                    "type_id": {
                        "type": "string"
                    },
                    "confidence": {
                        "type": "number",
                        "format": "float"
                    }
                }
            },
            "DeleteClauseResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "doc_id": {
                        "type": "string"
                    },
                    "deleted_clause_index": {
                        "type": "integer"
                    },
                    "deleted_clause_type": {
                        "type": "string"
                    },
                    "remaining_clauses": {
                        "type": "integer"
                    }
                }
            },

            # Field schemas
            "Field": {
                "type": "object",
                "properties": {
                    "field_id": {
                        "type": "string"
                    },
                    "field_name": {
                        "type": "string"
                    },
                    "values": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "clause_indices": {
                        "type": "array",
                        "items": {
                            "type": "integer"
                        }
                    }
                }
            },
            "FieldsResponse": {
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string"
                    },
                    "pdf_file": {
                        "type": "string"
                    },
                    "total_fields": {
                        "type": "integer"
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/Field"
                        }
                    }
                }
            },
            "SingleFieldResponse": {
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string"
                    },
                    "field": {
                        "$ref": "#/components/schemas/Field"
                    }
                }
            },
            "FieldResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "doc_id": {
                        "type": "string"
                    },
                    "field_id": {
                        "type": "string"
                    },
                    "field": {
                        "$ref": "#/components/schemas/Field"
                    },
                    "total_fields": {
                        "type": "integer"
                    }
                }
            },
            "AddFieldRequest": {
                "type": "object",
                "required": ["field_name"],
                "properties": {
                    "field_id": {
                        "type": "string",
                        "description": "Optional field ID (auto-generated if not provided)"
                    },
                    "field_name": {
                        "type": "string",
                        "description": "Field name"
                    },
                    "values": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "default": []
                    },
                    "clause_indices": {
                        "type": "array",
                        "items": {
                            "type": "integer"
                        },
                        "default": []
                    }
                }
            },
            "UpdateFieldRequest": {
                "type": "object",
                "properties": {
                    "field_name": {
                        "type": "string"
                    },
                    "values": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "clause_indices": {
                        "type": "array",
                        "items": {
                            "type": "integer"
                        }
                    }
                }
            },
            "DeleteFieldResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "doc_id": {
                        "type": "string"
                    },
                    "deleted_field_id": {
                        "type": "string"
                    },
                    "deleted_field_name": {
                        "type": "string"
                    },
                    "remaining_fields": {
                        "type": "integer"
                    }
                }
            },

            # Lease Upload schemas
            "ImportFromFoldersRequest": {
                "type": "object",
                "description": "Request body for importing PDFs from folders",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Custom path to input_folders directory",
                        "default": "input_folders"
                    },
                    "folder_name": {
                        "type": "string",
                        "description": "Process only this specific subfolder"
                    },
                    "auto_process": {
                        "type": "boolean",
                        "description": "Automatically trigger processing after import",
                        "default": False
                    }
                }
            },
            "ImportFromFoldersResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "input_path": {
                        "type": "string"
                    },
                    "folders_scanned": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "files_found": {
                        "type": "integer"
                    },
                    "files_imported": {
                        "type": "integer"
                    },
                    "files_skipped": {
                        "type": "integer"
                    },
                    "files_failed": {
                        "type": "integer"
                    },
                    "processing_started": {
                        "type": "boolean",
                        "description": "Whether auto-processing was started"
                    },
                    "details": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "file": {
                                    "type": "string"
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["imported", "skipped", "failed"]
                                },
                                "lease_id": {
                                    "type": "string"
                                },
                                "storage_type": {
                                    "type": "string"
                                },
                                "reason": {
                                    "type": "string"
                                },
                                "existing_id": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                }
            },
            "ListFoldersResponse": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string"
                    },
                    "total_folders": {
                        "type": "integer"
                    },
                    "total_pdf_files": {
                        "type": "integer"
                    },
                    "folders": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string"
                                },
                                "path": {
                                    "type": "string"
                                },
                                "pdf_count": {
                                    "type": "integer"
                                }
                            }
                        }
                    }
                }
            },
            "LeaseDocument": {
                "type": "object",
                "description": "Uploaded lease document with status tracking",
                "properties": {
                    "_id": {
                        "type": "string",
                        "description": "MongoDB document ID"
                    },
                    "original_filename": {
                        "type": "string",
                        "description": "Original PDF filename"
                    },
                    "storage_name": {
                        "type": "string",
                        "description": "Unique filename in storage"
                    },
                    "storage_location": {
                        "type": "string",
                        "description": "URL or path to stored file"
                    },
                    "storage_type": {
                        "type": "string",
                        "enum": ["azure", "local"],
                        "description": "Storage type used"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "processing", "processed", "failed"],
                        "description": "Processing status"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Upload timestamp"
                    },
                    "updated_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Last update timestamp"
                    },
                    "processed_at": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": True,
                        "description": "Processing completion timestamp"
                    },
                    "result_id": {
                        "type": "string",
                        "nullable": True,
                        "description": "ID of the processed result in cube_outputs collection"
                    },
                    "error_message": {
                        "type": "string",
                        "nullable": True,
                        "description": "Error message if processing failed"
                    }
                }
            },
            "LeaseUploadResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "lease_id": {
                        "type": "string",
                        "description": "MongoDB ID of the uploaded lease"
                    },
                    "original_filename": {
                        "type": "string"
                    },
                    "storage_name": {
                        "type": "string"
                    },
                    "storage_type": {
                        "type": "string",
                        "enum": ["azure", "local"]
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending"]
                    }
                }
            },
            "LeaseBatchUploadResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string"
                    },
                    "total": {
                        "type": "integer",
                        "description": "Total files in request"
                    },
                    "successful": {
                        "type": "integer",
                        "description": "Number of successfully uploaded files"
                    },
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "filename": {
                                    "type": "string"
                                },
                                "success": {
                                    "type": "boolean"
                                },
                                "lease_id": {
                                    "type": "string",
                                    "description": "Present if success is true"
                                },
                                "storage_name": {
                                    "type": "string"
                                },
                                "storage_type": {
                                    "type": "string"
                                },
                                "status": {
                                    "type": "string"
                                },
                                "error": {
                                    "type": "string",
                                    "description": "Present if success is false"
                                }
                            }
                        }
                    }
                }
            },
            "LeasesListResponse": {
                "type": "object",
                "properties": {
                    "leases": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/LeaseDocument"
                        }
                    },
                    "total": {
                        "type": "integer",
                        "description": "Total number of leases matching filter"
                    },
                    "page": {
                        "type": "integer"
                    },
                    "limit": {
                        "type": "integer"
                    },
                    "total_pages": {
                        "type": "integer"
                    }
                }
            },
            "ProcessingStartResponse": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Processing started"
                    },
                    "pending": {
                        "type": "integer",
                        "description": "Number of pending leases to process"
                    },
                    "batch_size": {
                        "type": "integer",
                        "description": "Number of files processed per batch",
                        "example": 2
                    }
                }
            },
            "ProcessingStatusResponse": {
                "type": "object",
                "properties": {
                    "is_processing": {
                        "type": "boolean",
                        "description": "Whether batch processing is currently running"
                    },
                    "message": {
                        "type": "string",
                        "description": "Status message (optional)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Status string (optional)"
                    },
                    "pending": {
                        "type": "integer",
                        "description": "Number of pending leases (optional)"
                    },
                    "counts": {
                        "type": "object",
                        "properties": {
                            "pending": {
                                "type": "integer"
                            },
                            "processing": {
                                "type": "integer"
                            },
                            "processed": {
                                "type": "integer"
                            },
                            "failed": {
                                "type": "integer"
                            },
                            "total": {
                                "type": "integer"
                            }
                        }
                    }
                }
            }
        }
    }
}
