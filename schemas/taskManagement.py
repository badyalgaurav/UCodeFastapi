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
    description:Optional[str]=None

    
    
class SubmitTask(BaseModel):
    userId: Optional[str] = None
    classId: Optional[str] = None
    contentId:Optional[str] = None
    submittedDate:Optional[str] = None
    score:Optional[str] = None
    text: Optional[str] = None
    isActive:Optional[bool]=True