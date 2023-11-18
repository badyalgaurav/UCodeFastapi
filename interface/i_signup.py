from fastapi import FastAPI, HTTPException, Form, UploadFile, File, BackgroundTasks, Request, Depends, APIRouter
from passlib.hash import bcrypt
from pymongo import MongoClient
import datetime
from fastapi.responses import StreamingResponse, FileResponse
from bson import ObjectId, json_util
import io
import json
import pandas as pd
from pymongo.errors import DuplicateKeyError
# from config import settings
from schemas.taskManagement import SubmitTask, TaskManagement
from typing import Optional, List
import os
router = APIRouter(prefix="/user_content_management", tags=["Authentication"])

# MONGODB_CONN_STR = settings.MONGODB_CONN_STR
MONGODB_CONN_STR = "mongodb://interx:interx%40504@server.interxlab.io:15115/admin"
# Connection to MongoDB
client = MongoClient(MONGODB_CONN_STR)

# database
db = client["UUAABBCC"]

# collections
users_collection = db["users"]
accounts_collection = db["accounts"]
contents_collection = db["contents"]
draft_collection = db["draftContents"]
class_collection = db["class"]
notes_collection = db["notes"]
submit_assignment_collection = db["submitAssignment"]

# video_path = None
# text_path = None


async def background_work(video: UploadFile):
    # global video_path
    # Save the uploaded video and text file to a specific directory
    try:
        video_path = f"/var/www/"

        if not os.path.exists(video_path):
            os.makedirs(video_path)
        video_path_video = f"/var/www/{video.filename}"
        with open(video_path_video, "wb") as video_file:
            video_file.write(await video.read())
        return {"video_path": video_path_video}
    except Exception as e:
        return {"video_path": ""}
# Endpoint for user signup


@router.post("/signup")
async def signup(username: str, first_name: str, last_name: str, password: str, email_id: str, phone_number: int, class_id: str, account_id: str):

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
async def login(email: str, password: str):
    user = users_collection.find_one({"emailId": email})
    user["_id"] = str(user["_id"])
    user["classId"] = str(user["classId"])
    user_list = [user]
    if user and bcrypt.verify(password, user["passwordHash"]):
        return {"data": user, "Message": "success"}
    raise HTTPException(status_code=401, detail="Invalid username or password")


# Endpoint for inserting a video (schedules the background task)
@router.post("/insert_video")
async def insert_video(video: UploadFile):
    res = await background_work(video)
    return res


async def insert_task_info_bg(model: TaskManagement):
    try:
        # video_path= await background_work(video=video)
        user_id = ObjectId(model.userId)
        class_id = ObjectId(model.classId)
        # global video_path
        # global text_path
        contents = {
            "userId": user_id,
            "classId": class_id,
            "textFilePath": None,
            "text": model.text,
            "videoPath": model.videoPath,
            "taskName": model.taskName,
            "description":model.description
        }
        # insert the document into contents collection
        result = contents_collection.insert_one(contents)

        # Get the inserted _id from the result object
        # content_id = result.inserted_id

        return "sucess"
    except:
        return "failure"
# Endpoint for inserting task information


@router.post("/insert_task_info")
async def insert_task_info(model: TaskManagement):
    res = await insert_task_info_bg(model)
    return {"message": res}
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
async def get_contents_list(user_id: str, class_id: Optional[str] = None):

    user = ObjectId(user_id)
    contents = {
        "userId": user
    }
    if class_id:
        classid = ObjectId(class_id)
        contents = {
            "userId": user,
            "classId": classid
        }

    cursor = contents_collection.find(contents)
    df = pd.DataFrame(list(cursor))
    if not df.empty:
        df["_id"] = df["_id"].astype(str)
        df["userId"] = df["userId"].astype(str)
        df["classId"] = df["classId"].astype(str)
        parsed_df = json.loads(df.to_json(orient="records"))
        return {"data": parsed_df}
    else:
        return {"data": []}

# Endpoint for getting a list of contents based on class ID


@router.get("/contents_list_by_class_id")
async def contents_list_by_class_id(class_id: str):

    classid = ObjectId(class_id)
    contents = {
        "classId": classid
    }

    cursor = contents_collection.find(contents)
    df = pd.DataFrame(list(cursor))
    if not df.empty:
        df["_id"] = df["_id"].astype(str)
        df["userId"] = df["userId"].astype(str)
        df["classId"] = df["classId"].astype(str)
        parsed_df = json.loads(df.to_json(orient="records"))
        return {"data": parsed_df}
    else:
        return {"data": []}

# Endpoint for getting a list of draft based on user ID


@router.get("/draft_list_by_user_id")
async def draft_list_by_user_id(userId: str):

    userId = ObjectId(userId)
    contents = {
        "userId": userId
    }

    cursor = draft_collection.find(contents)
    df = pd.DataFrame(list(cursor))
    if not df.empty:
        df["_id"] = df["_id"].astype(str)
        df["userId"] = df["userId"].astype(str)
        df["classId"] = df["classId"].astype(str)
        parsed_df = json.loads(df.to_json(orient="records"))
        return {"data": parsed_df}
    else:
        return {"data": []}

# Endpoint for getting a list of draft based on user ID


@router.get("/get_draft_by_id")
async def get_draft_by_id(draftId: str):

    _id = ObjectId(draftId)
    contents = {
        "_id": _id
    }
    cursor = draft_collection.find_one(contents)
    df = cursor
    if df:
        df["_id"] = str(df["_id"])
        df["userId"] = str(df["userId"])
        df["classId"] = str(df["classId"])
        return {"data": df}
    else:
        return {"data": []}

# Endpoint for getting a list of contents based on user ID and optional class ID


@router.get("/content_by_id")
async def get_contents_by_id(content_id: str):

    content_id = ObjectId(content_id)
    filter = {
        "_id": content_id
    }

    cursor = contents_collection.find_one(filter)
    df = cursor
    if df:
        df["_id"] = str(df["_id"])
        df["userId"] = str(df["userId"])
        df["classId"] = str(df["classId"])
        return {"data": df}
    else:
        return {"data": []}

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
async def insert_notes(content: str, header: str, user_id: str, content_id: str, duration: str):
    # Get the current date and time
    timestamp = datetime.datetime.utcnow()

    notes = {
        "content": content,
        "header": header,
        "userId": ObjectId(user_id),
        "contentId": ObjectId(content_id),
        "duration": duration,
        "isActive": True,
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


@router.get("/video")
async def get_video(video_path):
    # Replace 'path_to_video.mp4' with the actual path to your video file.
    # video_path = "/var/www/1.mp4"
    return FileResponse(video_path, media_type="video/mp4")


@router.delete("/delete_content")
async def delete_content_by_id(content_id: str):

    content_id = ObjectId(content_id)
    filter = {
        "_id": content_id
    }

    ack = contents_collection.delete_one(filter)
    return "success"


@router.post("/submit_assignment")
async def submit_assignment(model: SubmitTask):
    try:
        # video_path= await background_work(video=video)
        user_id = ObjectId(model.userId)
        class_id = ObjectId(model.classId)
        contentId = ObjectId(model.contentId)
        # global video_path
        # global text_path
        contents = {
            "userId": user_id,
            "classId": class_id,
            "contentId": contentId,
            "text": model.text,
            "submittedDate": str(datetime.datetime.utcnow()),
            "score": "NA"
        }
        # insert the document into contents collection
        result = submit_assignment_collection.insert_one(contents)

        # Get the inserted _id from the result object
        # content_id = result.inserted_id

        return "sucess"
    except:
        return "failure"