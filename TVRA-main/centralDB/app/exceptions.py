class EvidenceNotFound(Exception):
    """Exception raised when evidence is not found in the database."""
    
    def __init__(self, category: str, version_id: int, filename: str = None):
        self.category = category
        self.version_id = version_id
        self.filename = filename
        
        if filename:
            if version_id > 0:
                self.message = f"Evidence not found for category '{category}', filename '{filename}' with version_id {version_id}"
            else:
                self.message = f"Evidence not found for category '{category}', filename '{filename}'"
        else:
            self.message = f"Evidence not found for category '{category}' with version_id {version_id}"
            
        super().__init__(self.message) 