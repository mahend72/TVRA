import os
import json
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Query, Body, Depends
from fastapi.responses import FileResponse, JSONResponse, Response

from app import storage
from app.exceptions import EvidenceNotFound

# Initialize FastAPI app
app = FastAPI(
    title="O-ETB Evidence Management System",
    description="API for storing and retrieving evidence files for assurance cases",
    version="1.0.0",
)


@app.post("/upload/{category}")
async def upload_evidence(
    category: str,
    file: UploadFile = File(...),
    comment: str = Form(""),
    original_filename: str = Form(None),
):
    """
    Upload a new evidence file.
    
    Args:
        category: Category of the evidence
        file: File to upload
        comment: Optional comment about the evidence
        original_filename: Optional original filename (if not provided, uses file.filename)
        
    Returns:
        JSON with filename, version_id and timestamp
    """
    try:
        result = await storage.save_evidence(
            category, file, comment, original_filename
        )
        
        # Get the saved evidence including hash
        evidence = storage.read_evidence(category, result["filename"], result["version_id"])
        
        return {
            "status": "success",
            "filename": result["filename"],
            "version_id": result["version_id"],
            "timestamp": result["timestamp"],
            "sha256_hash": evidence.get("sha256_hash", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/upload-json/{category}")
async def upload_json_evidence(
    category: str,
    json_data: Dict[str, Any] = Body(...),
    comment: str = "",
    original_filename: str = None,
):
    """
    Upload JSON data directly as evidence.
    
    Args:
        category: Category of the evidence
        json_data: JSON data to upload
        comment: Optional comment about the evidence
        original_filename: Optional original filename (defaults to 'data.json')
        
    Returns:
        JSON with filename, version_id and timestamp
    """
    try:
        # If no original filename provided, use a default
        if not original_filename:
            original_filename = "data.json"
            
        # Ensure the filename has .json extension
        if not original_filename.endswith('.json'):
            original_filename += '.json'
            
        result = await storage.save_json_evidence(
            category, json_data, comment, original_filename
        )
        
        # Get the saved evidence including hash
        evidence = storage.read_evidence(category, result["filename"], result["version_id"])
        
        return {
            "status": "success",
            "filename": result["filename"],
            "version_id": result["version_id"],
            "timestamp": result["timestamp"],
            "sha256_hash": evidence.get("sha256_hash", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading JSON data: {str(e)}")


@app.get("/download/{category}/{filename}")
async def download_evidence(
    category: str, 
    filename: str, 
    version_id: Optional[int] = None,
    as_json: bool = False
):
    """
    Download an evidence file, optionally specifying a version.
    
    Args:
        category: Category of the evidence
        filename: Name of the file
        version_id: Optional version ID (if None, returns latest version)
        as_json: If true and file is JSON, returns parsed JSON content
        
    Returns:
        Evidence file with SHA-256 hash in X-SHA256-Hash header or JSON content
    """
    try:
        evidence = storage.read_evidence(category, filename, version_id)
        
        # Verify file integrity
        if "sha256_hash" in evidence and os.path.exists(evidence["stored_path"]):
            if not storage.verify_file_hash(evidence["stored_path"], evidence["sha256_hash"]):
                raise HTTPException(status_code=500, detail="File integrity check failed: hash mismatch")
        
        # Check if we should return JSON directly
        #if as_json or (evidence["original_filename"].lower().endswith('.json')):
        if as_json:
            # Try to parse the file as JSON
            try:
                with open(evidence["stored_path"], "r") as f:
                    json_content = json.load(f)
                
                # Create a JSON response
                response = JSONResponse(content=json_content)
                
                # Add SHA-256 hash to response headers
                if "sha256_hash" in evidence:
                    response.headers["X-SHA256-Hash"] = evidence["sha256_hash"]
                
                return response
            except json.JSONDecodeError:
                # If we can't parse as JSON but as_json is explicitly True, return an error
                if as_json:
                    raise HTTPException(status_code=400, detail="File is not valid JSON")
        
        # Default to binary file response
        response = FileResponse(
            path=evidence["stored_path"],
            filename=evidence["original_filename"],
            media_type="application/octet-stream",
        )
        
        # Add SHA-256 hash to response headers
        if "sha256_hash" in evidence:
            response.headers["X-SHA256-Hash"] = evidence["sha256_hash"]
        
        return response
    except EvidenceNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")


@app.get("/list/{category}")
async def list_evidence_items(category: str):
    """
    List all evidence records within a specific category, grouped by filename.
    
    Args:
        category: Category to list evidence for
        
    Returns:
        Dictionary with filenames as keys and lists of version metadata as values
    """
    try:
        records = storage.list_evidence(category)
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing evidence: {str(e)}")


@app.delete("/delete/{category}/{filename}")
async def delete_evidence_item(
    category: str, 
    filename: str,
    version_id: Optional[int] = None
):
    """
    Delete evidence records and files for a specific filename.
    If version_id is provided, only that version is deleted.
    Otherwise, all versions of the file are deleted.
    
    Args:
        category: Category of the evidence
        filename: Name of the file
        version_id: Optional version ID (if None, deletes all versions)
        
    Returns:
        Success message
    """
    try:
        storage.delete_evidence(category, filename, version_id)
        return {"status": "success"}
    except EvidenceNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting evidence: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 