from fastapi import UploadFile,File
from pydantic import BaseModel
from typing import Optional

# Pydantic model for the request data
class TaskManagement(BaseModel):
    userId: str
    classId: str
    videoPath: Optional[str] = None
    text: Optional[str] = None
    taskName: Optional[str] = None

    
    
