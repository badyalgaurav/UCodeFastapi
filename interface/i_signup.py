from fastapi import FastAPI, HTTPException,Form, UploadFile, File, BackgroundTasks, Request, Depends, APIRouter
from passlib.hash import bcrypt
from pymongo import MongoClient
import datetime 
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
db = client["UUAABBCC"]

# collections
users_collection = db["users"]
accounts_collection = db["accounts"]
contents_collection = db["contents"]
class_collection = db["class"]
notes_collection = db["notes"]
video_path = None
text_path = None

async def background_work(video: UploadFile):
    global video_path
    # Save the uploaded video and text file to a specific directory
    video_path = f"C:/Users/HIMANI/Desktop/{video.filename}"

    with open(video_path, "wb") as video_file: 
        video_file.write(await video.read())
    return {"video stored please run next api" ,video_path}

# Endpoint for user signup
@router.post("/signup")
async def signup(username: str, first_name:str, last_name: str, password: str, email_id: str, phone_number: int, class_id: str, account_id: str):
    
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
        "classId": ObjectId(class_id), 
        "accountId": account_id
        }

    try:
        # Insert the user document into the users collection
        users_collection.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "Signup successful"}

# Endpoint for user login
@router.get("/login")
async def login(username: str, password: str):
    user = users_collection.find_one({"userName": username})
    user_list = [user]
    if user and bcrypt.verify(password, user["passwordHash"]):
        # Fetch the user's content_id (foreign key)
        user_id = user.get("_id")
        # Check if contentId is null in the other collection
        existing_document = contents_collection.find_one({"userId": user_id})

        if existing_document:
            # MongoDB aggregation pipeline using $lookup
            pipeline = [
                {"$match": {"_id": user_id}},
                {"$lookup": {
                    "from": "contents",
                    "localField": "_id",
                    "foreignField": "userId",
                    "as": "user_info"
                }},
                {"$unwind": "$user_info"},
                {"$lookup": {
                    "from": "class",
                    "localField": "classId",
                    "foreignField": "_id",
                    "as": "class_info"
                }},
                {"$unwind": "$class_info"},
                {
                    "$project": {
                        "firstName": 1,
                        "lastName": 1,
                        "emailId": 1,
                        "phoneNumber": 1,
                        "classId": 1,
                        "class": "$class_info.class",
                        "section": "$class_info.section",
                        "accountId": 1,
                        "contentId": 1,
                        "videoPath": "$user_info.videoPath",
                        "textFilePath": "$user_info.textFilePath"
                    }
                }
            ]

            # Perform aggregation using the pipeline
            cursor = users_collection.aggregate(pipeline)
            df = pd.DataFrame(cursor)
            df = df.astype(str) 
            parsed_df = json.loads(df.to_json(orient="records"))
            return {"Message": "Login Successful", "data": parsed_df}
        df = pd.DataFrame(user_list)
        df["_id"]=df["_id"].astype(str)
        df["classId"]=df["classId"].astype(str) 
        df=df.drop(["passwordHash"], axis=1)
        parsed_df = json.loads(df.to_json(orient="records"))
        return {"data": parsed_df, "Message": "No available contents for the user", }
    raise HTTPException(status_code=401, detail="Invalid username or password")


# Endpoint for inserting a video (schedules the background task)
@router.post("/insert_video")
async def insert_video(background_tasks:BackgroundTasks, video: UploadFile):
    background_tasks.add_task(background_work, video)
    # return {"message": "Notification sent in the background"}

# Endpoint for inserting task information
@router.post("/insert_task_info")
async def insert_task_info(model: TaskManagement):
    user_id = ObjectId(model.userId)
    class_id = ObjectId(model.classId)
    global video_path
    global text_path
    contents = { 
        "userId": user_id,
        "classId": class_id,
        "textFilePath": text_path,
        "text": model.text,
        "videoPath": video_path,        
    }
    #insert the document into contents collection
    result = contents_collection.insert_one(contents)

     # Get the inserted _id from the result object
    content_id = result.inserted_id
     
    return {"message": "Inserted Successfully", "_id": content_id}
    # return {"message": "Notification sent in the background"}


# Endpoint for viewing videos by user ID
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


# Endpoint for getting a list of contents based on user ID and optional class ID
@router.get("/contents_list")
async def get_contents_list(user_id: str, class_id: Optional[str]):
    user = ObjectId(user_id)
    classid = ObjectId(class_id)
    contents = {
        "userId": user,
        "classId": classid
    }
    cursor = contents_collection.find(contents)
    df = pd.DataFrame(list(cursor))
    df["_id"] = df["_id"].astype(str)
    df["userId"] = df["userId"].astype(str)
    df["classId"] = df["classId"].astype(str)
    parsed_df = json.loads(df.to_json(orient="records"))
    return {"data": parsed_df}

# Endpoint for getting a list of classes
@router.get("/class_list")
async def get_class_list():
    cursor = class_collection.find()
    df = pd.DataFrame(list(cursor))
    df["_id"] = df["_id"].astype(str)
    parsed_df = json.loads(df.to_json(orient="records"))
    return {"data": parsed_df}

# Endpoint for inserting notes
@router.post("/insert_notes")
async def insert_notes(content: str, header: str, user_id: str, content_id: str, is_active: bool):
    # Get the current date and time
    timestamp = datetime.datetime.utcnow()

    notes = {
        "content": content,
        "header": header,
        "userId": ObjectId(user_id),
        "contentId": ObjectId(content_id),
        "isActive": is_active,
        "timestamp": timestamp
    }

    notes_collection.insert_one(notes)
    return {"message": "Inserted Successfully"}

# Endpoint for getting notes based on user ID and content ID
@router.get("/get_notes")
async def get_notes(user_id: str, content_id: str):
    user_id = ObjectId(user_id)
    content_id = ObjectId(content_id)

    notes = {
        "userId": user_id,
        "contentId": content_id
    }

    cursor = notes_collection.find(notes)
    df = pd.DataFrame(list(cursor))
    df = df.astype(str)
    parsed_df = json.loads(df.to_json(orient="records"))
    return {"data": parsed_df}

# Endpoint for deleting notes based on note ID
@router.get("/delete_notes")
async def delete_notes(note_id: str):
    notes_collection.update_one(
        {"_id": ObjectId(note_id)},
        {"$set": {"isActive": False}}
    )

    return {"Deleted Successfully"}

