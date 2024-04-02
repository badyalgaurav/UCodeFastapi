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
    
class CameraInfo(BaseModel):
    cName: Optional[str] = None
    cEmail: Optional[str] = None
    cAddress: Optional[str] = None
    cPassword: Optional[str] = None
    telegramGroupName: Optional[str] = None

    eName: Optional[str] = None
    eEmail: Optional[str] = None
    eAddress: Optional[str] = None

    cameraInfo: Optional[str] = None
    aiPerSecondRatio: Optional[int] = None
