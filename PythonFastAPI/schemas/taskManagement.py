from pydantic import BaseModel
from typing import Optional

# Pydantic model for the request data
class TaskManagement(BaseModel):
    userId: str
    classId: str
    textFilePath: Optional[str] = None
    text: Optional[str] = None
    
    
