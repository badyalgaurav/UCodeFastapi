from fastapi import FastAPI, HTTPException, Form, UploadFile, File, BackgroundTasks, Request, Depends, APIRouter
from passlib.hash import bcrypt
import uvicorn
from bson.objectid import ObjectId
# from interface.interfaces import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
# from config import settings
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
app = FastAPI(debug=True)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}



@app.get("/hello32/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.get("/login")
async def login(email: str, password: str):
    user = users_collection.find_one({"emailId": email})
    user["_id"] = str(user["_id"])
    user["classId"] = str(user["classId"])
    user_list = [user]
    if user and bcrypt.verify(password, user["passwordHash"]):
        return {"data": user, "Message": "success"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

@app.on_event("startup")
async def startup():
    print("startup")


@app.on_event("shutdown")
async def shutdown():
    print("shutdown")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# app.include_router(api_router)

# if __name__ == '__main__':
#     uvicorn.run("main:app",
#                 host="0.0.0.0",
#                 port=8000,
#                 reload=True)
