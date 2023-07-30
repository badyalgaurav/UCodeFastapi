from fastapi import FastAPI, HTTPException,Form, UploadFile, File, BackgroundTasks, Request, Depends, APIRouter
from passlib.hash import bcrypt
from pymongo import MongoClient
from fastapi.responses import StreamingResponse, FileResponse
from bson import ObjectId, json_util
import io, json
import pandas as pd
from pymongo.errors import DuplicateKeyError
from config import settings
from schemas.taskManagement import TaskManagement
from typing import Optional, List
router = APIRouter(prefix="/user_content_management", tags=["Authentication"])

MONGODB_CONN_STR = settings.MONGODB_CONN_STR

# Connection to MongoDB
client = MongoClient(MONGODB_CONN_STR)

# database
db = client["apidb"]

# collections
users_collection = db["users"]
accounts_collection = db["accounts"]
contents_collection = db["contents"]
class_collection = db["class"]
video_path = None
text_path = None

async def background_work(video: UploadFile):
    global video_path
    # Save the uploaded video and text file to a specific directory
    video_path = f"C:/Users/HIMANI/Desktop/{video.filename}"

    with open(video_path, "wb") as video_file: 
        video_file.write(await video.read())
    return {video_path}

@router.post("/signup")
async def signup(username: str, first_name:str, last_name: str, password: str, email_id: str, phone_number: int, class_id: int, account_id: str):
    
    # Check if the username is already taken
    existing_user = users_collection.find_one({"userName": username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password using bcrypt
    password_hash = bcrypt.hash(password)

    # Create a new user document
    user = {
        "userName": username, 
        "firstName": first_name,
        "lastName": last_name,
        "passwordHash": password_hash, 
        "emailId": email_id, 
        "phoneNumber": phone_number, 
        "classId": class_id, 
        "accountId": account_id
        }

    try:
        # Insert the user document into the users collection
        users_collection.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "Signup successful"}


@router.get("/login")
async def login(username: str, password: str):
    user = users_collection.find_one({"userName": username})

    if user and bcrypt.verify(password, user["passwordHash"]):
        # Fetch the user's content_id (foreign key)
        content_id = user.get("contentId")
        if content_id:
            # MongoDB aggregation pipeline using $lookup
            pipeline = [
                {"$match": {"_id": ObjectId(content_id)}},
                {"$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "contentId",
                    "as": "user_info"
                }},
                {"$unwind": "$user_info"},
                {
                    "$project": {
                        "firstName": "$user_info.firstName",
                        "lastName": "$user_info.lastName",
                        "emailId": "$user_info.emailId",
                        "phoneNumber": "$user_info.phoneNumber",
                        "classId": "$user_info.classId",
                        "accountId": "$user_info.accountId",
                        "videoPath": 1,
                        "textFilePath": 1
                    }
                }
            ]

            # Perform aggregation using the pipeline
            cursor = contents_collection.aggregate(pipeline)
            df = pd.DataFrame(cursor)
            df["_id"]=df["_id"].astype(str)
            parsed_df = json.loads(df.to_json(orient="records"))
            return {"Message": "Login Successful", "data": parsed_df}
    raise HTTPException(status_code=401, detail="Invalid username or password")


@router.post("/insert_video")
async def insert_video(background_tasks:BackgroundTasks, video: UploadFile):
    background_tasks.add_task(background_work, video)
    # return {"message": "Notification sent in the background"}

@router.post("/insert_task_info")
async def insert_task_info(model: TaskManagement):
    user_id = ObjectId(model.userId)
    global video_path
    global text_path
    contents = { 
        "userId": user_id,
        "classId": model.classId,
        "textFilePath": text_path,
        "text": model.text,
        "videoPath": video_path,        
    }
    #insert the document into contents collection
    contents_collection.insert_one(contents)

    return {"message": "Inserted Successfully"}
    # return {"message": "Notification sent in the background"}


@router.get("/view_videos")
async def view_videos_textfiles(user_id: str):
    user_id = ObjectId(user_id)

    # Retrieve the video and text file paths from the database based on the IDs
    video = contents_collection.find_one({"userId": user_id})
    
    if not video:
        return {"message": "Video not found"}
    
    # Retrieve the video path from the video document
    video_path = video["videoPath"]

    # Read the video file and return it as a response
    with open(video_path, "rb") as video_file:
        video_data = video_file.read()

    return StreamingResponse(io.BytesIO(video_data), media_type="video/mp4")

@router.get("/contents_list")
async def get_contents_list(user_id: str, class_id: str):
    user = ObjectId(user_id)
    classid = ObjectId(class_id)
    contents = { 
        "userId": user,
        "classId": classid       
    }
    cursor = contents_collection.find(contents)
    df =  pd.DataFrame(list(cursor))
    df["_id"]=df["_id"].astype(str)
    df["userId"]=df["userId"].astype(str)
    df["classId"]=df["classId"].astype(str)
    parsed_df = json.loads(df.to_json(orient="records"))
    return {"data": parsed_df}

    



    

