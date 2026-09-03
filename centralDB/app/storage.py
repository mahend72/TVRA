import os
import json
import shutil
import hashlib
import re
import io
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

from fastapi import UploadFile
from tinydb import TinyDB, Query

from app.exceptions import EvidenceNotFound

# Constants
DATA_DIR = "/app/data"
FILES_DIR = os.path.join(DATA_DIR, "files")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")

# Ensure data directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

# Initialize TinyDB
db = TinyDB(METADATA_FILE)


def compute_sha256(content: bytes) -> str:
    """
    Compute SHA-256 hash of file content.
    
    Args:
        content: File content as bytes
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()


def secure_filename(filename: str) -> str:
    """
    Sanitize a filename to be safe for storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace spaces with underscores and remove problematic characters
    return re.sub(r'[^\w\.-]', '_', filename)


async def save_json_evidence(
    category: str, 
    json_data: Dict[str, Any], 
    comment: str = "", 
    original_filename: str = "data.json"
) -> Dict[str, Any]:
    """
    Save JSON data directly as evidence.
    
    Args:
        category: Category of the evidence
        json_data: JSON data to upload
        comment: Optional comment about the evidence
        original_filename: Original filename (defaults to 'data.json')
        
    Returns:
        Dictionary containing version_id, timestamp, and filename
    """
    # Ensure category directory exists
    category_dir = os.path.join(FILES_DIR, category)
    os.makedirs(category_dir, exist_ok=True)
    
    # Ensure the filename has .json extension
    if not original_filename.endswith('.json'):
        original_filename += '.json'
        
    # Sanitize filename for storage
    safe_filename = secure_filename(original_filename)
    
    # Query for existing versions of this file
    Evidence = Query()
    existing_files = db.search(
        (Evidence.category == category) & 
        (Evidence.filename == safe_filename)
    )
    
    # Determine next version_id for this filename
    if not existing_files:
        next_version_id = 1
    else:
        next_version_id = max([file_doc.get('version_id', 0) for file_doc in existing_files]) + 1
    
    # Construct file path with filename and version
    stored_path = os.path.join(category_dir, f"{safe_filename}_v{next_version_id}.json")
    
    # Convert JSON data to a properly formatted string with indentation
    json_content = json.dumps(json_data, indent=2)
    content_bytes = json_content.encode('utf-8')
    
    # Compute SHA-256 hash
    sha256_hash = compute_sha256(content_bytes)
    
    # Save the JSON content to a file
    with open(stored_path, "wb") as f:
        f.write(content_bytes)
    
    # Generate timestamp
    timestamp = datetime.now().isoformat()
    
    # Create and insert document
    document = {
        "category": category,
        "version_id": next_version_id,
        "filename": safe_filename,
        "original_filename": original_filename,
        "timestamp": timestamp,
        "comment": comment,
        "stored_path": stored_path,
        "sha256_hash": sha256_hash
    }
    
    db.insert(document)
    
    return {
        "version_id": next_version_id, 
        "timestamp": timestamp,
        "filename": safe_filename
    }


async def save_evidence(
    category: str, 
    file: UploadFile, 
    comment: str = "", 
    original_filename: str = None
) -> Dict[str, Any]:
    """
    Save evidence file to storage and record metadata in TinyDB.
    
    Args:
        category: Category of the evidence
        file: Uploaded file
        comment: Optional comment about the evidence
        original_filename: Optional original filename (if not provided, uses file.filename)
        
    Returns:
        Dictionary containing version_id, timestamp, and filename
    """
    # Ensure category directory exists
    category_dir = os.path.join(FILES_DIR, category)
    os.makedirs(category_dir, exist_ok=True)
    
    # Use provided original_filename or file.filename
    if original_filename is None:
        original_filename = file.filename
    
    # Sanitize filename for storage
    safe_filename = secure_filename(original_filename)
    
    # Get file extension
    _, file_extension = os.path.splitext(original_filename)
    
    # Query for existing versions of this file
    Evidence = Query()
    existing_files = db.search(
        (Evidence.category == category) & 
        (Evidence.filename == safe_filename)
    )
    
    # Determine next version_id for this filename
    if not existing_files:
        next_version_id = 1
    else:
        next_version_id = max([file_doc.get('version_id', 0) for file_doc in existing_files]) + 1
    
    # Construct file path with filename and version
    stored_path = os.path.join(category_dir, f"{safe_filename}_v{next_version_id}{file_extension}")
    
    # Read the file content
    content = await file.read()
    
    # Compute SHA-256 hash
    sha256_hash = compute_sha256(content)
    
    # Save the file
    with open(stored_path, "wb") as f:
        f.write(content)
    
    # Generate timestamp
    timestamp = datetime.now().isoformat()
    
    # Create and insert document
    document = {
        "category": category,
        "version_id": next_version_id,
        "filename": safe_filename,
        "original_filename": original_filename,
        "timestamp": timestamp,
        "comment": comment,
        "stored_path": stored_path,
        "sha256_hash": sha256_hash
    }
    
    db.insert(document)
    
    return {
        "version_id": next_version_id, 
        "timestamp": timestamp,
        "filename": safe_filename
    }


def read_evidence(
    category: str, 
    filename: str, 
    version_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Read evidence metadata and return file information.
    
    Args:
        category: Category of the evidence
        filename: Name of the file
        version_id: Optional version ID (if None, returns latest version)
        
    Returns:
        Dictionary containing evidence metadata
        
    Raises:
        EvidenceNotFound: If evidence is not found
    """
    Evidence = Query()
    
    if version_id:
        # Query for specific version
        result = db.search(
            (Evidence.category == category) & 
            (Evidence.filename == filename) & 
            (Evidence.version_id == version_id)
        )
        
        if not result:
            raise EvidenceNotFound(category, version_id, filename)
            
        return result[0]
    else:
        # Query for latest version
        files = db.search(
            (Evidence.category == category) & 
            (Evidence.filename == filename)
        )
        
        if not files:
            raise EvidenceNotFound(category, 0, filename)
        
        # Sort by version_id and return the latest
        files.sort(key=lambda x: x.get('version_id', 0), reverse=True)
        return files[0]


def verify_file_hash(file_path: str, expected_hash: str) -> bool:
    """
    Verify the hash of a file.
    
    Args:
        file_path: Path to the file
        expected_hash: Expected SHA-256 hash
        
    Returns:
        True if hash matches, False otherwise
    """
    with open(file_path, "rb") as f:
        content = f.read()
        
    actual_hash = compute_sha256(content)
    return actual_hash == expected_hash


def list_evidence(category: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all evidence records for a category, grouped by filename.
    
    Args:
        category: Category to list evidence for
        
    Returns:
        Dictionary with filenames as keys and lists of version metadata as values
    """
    Evidence = Query()
    results = db.search(Evidence.category == category)
    
    # Group by filename
    files_by_name = {}
    for item in results:
        filename = item.get("filename")
        if filename not in files_by_name:
            files_by_name[filename] = []
        
        files_by_name[filename].append({
            "version_id": item.get("version_id"),
            "original_filename": item.get("original_filename"),
            "timestamp": item.get("timestamp"),
            "comment": item.get("comment", ""),
            "sha256_hash": item.get("sha256_hash", ""),
            "is_json": item.get("original_filename", "").lower().endswith('.json')
        })
    
    # Sort versions within each filename
    for filename in files_by_name:
        files_by_name[filename].sort(key=lambda x: x.get("version_id"))
    
    return files_by_name


def delete_evidence(
    category: str, 
    filename: str, 
    version_id: Optional[int] = None
) -> bool:
    """
    Delete evidence file and metadata.
    
    Args:
        category: Category of the evidence
        filename: Name of the file
        version_id: Optional version ID (if None, deletes all versions)
        
    Returns:
        True if successful
        
    Raises:
        EvidenceNotFound: If evidence is not found
    """
    Evidence = Query()
    
    if version_id:
        # Delete specific version
        result = db.search(
            (Evidence.category == category) & 
            (Evidence.filename == filename) & 
            (Evidence.version_id == version_id)
        )
        
        if not result:
            raise EvidenceNotFound(category, version_id, filename)
        
        # Delete file
        stored_path = result[0].get("stored_path")
        if os.path.exists(stored_path):
            os.remove(stored_path)
        
        # Remove from database
        db.remove(
            (Evidence.category == category) & 
            (Evidence.filename == filename) & 
            (Evidence.version_id == version_id)
        )
    else:
        # Delete all versions
        files = db.search(
            (Evidence.category == category) & 
            (Evidence.filename == filename)
        )
        
        if not files:
            raise EvidenceNotFound(category, 0, filename)
        
        # Delete all files
        for file_doc in files:
            stored_path = file_doc.get("stored_path")
            if os.path.exists(stored_path):
                os.remove(stored_path)
        
        # Remove from database
        db.remove(
            (Evidence.category == category) & 
            (Evidence.filename == filename)
        )
    
    return True 