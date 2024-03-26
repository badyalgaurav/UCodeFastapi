from fastapi import APIRouter
from pymongo import MongoClient
import datetime
import json
from schemas.taskManagement import CameraInfo
router = APIRouter(prefix="/geocam", tags=["geocam"])
MONGODB_CONN_STR = "mongodb://interx:interx%40504@server.interxlab.io:15115/admin"
# Connection to MongoDB
client = MongoClient(MONGODB_CONN_STR)


def b_setup_registration(data: CameraInfo):
    # database
    db = client["UUAABBCC"]
    coll = db["accountInfo"]
    d_dict = data.dict()
    parse_camera_info = json.loads(d_dict["cameraInfo"])
    d_dict["cameraInfo"] = parse_camera_info
    d_dict["notificationEmails"] = d_dict.get("notificationEmails").split(",")
    d_dict["notificationEmails"]=[x for x in d_dict["notificationEmails"] if x]
    d_dict["isActive"] = True
    d_dict["createdDateTime"] = datetime.datetime.now()
    # //convert to dict(data)
    coll.insert_one(d_dict)
    return True


def b_get_camera_credentials(email: str, password: str):
    # database
    db = client["UUAABBCC"]
    coll = db["accountInfo"]
    response = coll.find_one({"cEmail":email,"cPassword":password,"isActive":True}, {"_id": 0})
    return response


@router.post("/setup_registration")
async def setup_registration(data: CameraInfo):
    # send the data to mongodb
    b_setup_registration(data)
    return {"message": "Form submitted successfully"}


@router.get("/get_camera_credentials")
async def get_camera_credentials(email: str, password: str):
    # send the data to mongodb
    res = b_get_camera_credentials(email, password)
    return res
