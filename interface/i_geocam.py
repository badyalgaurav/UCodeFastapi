from fastapi import APIRouter
from pymongo import MongoClient
import datetime
import json
from schemas.taskManagement import CameraInfo
import requests
from config import settings
router = APIRouter(prefix="/geocam", tags=["geocam"])
MONGODB_CONN_STR = "mongodb://interx:interx%40504@server.interxlab.io:15115/admin"
TELEGRAM_BOT_URL=f"https://api.telegram.org/bot{settings.TELE_BOT_TOKEN}/getUpdates"
# Connection to MongoDB
client = MongoClient(MONGODB_CONN_STR)


async def b_setup_registration(data: CameraInfo):
    # database
    db = client["UUAABBCC"]
    coll = db["accountInfo"]
    d_dict = data.dict()
    parse_camera_info = json.loads(d_dict["cameraInfo"])
    d_dict["cameraInfo"] = parse_camera_info

    acc_alr_exists=coll.find_one({"cEmail":data.cEmail})
    if acc_alr_exists:
        return "account with same email already exists. Try different email for the customer."

    channel_id= await get_tele_channel_id(telegram_group_name=data.telegramGroupName)
    if channel_id:
        already_exist_channel_ids=coll.count_documents({"channelId":channel_id})
        if already_exist_channel_ids:
            return "Telegram group with same channel id already exists."
        
        d_dict["channelId"] = channel_id
        d_dict["telegramGroupName"] = data.telegramGroupName
        d_dict["isActive"] = True
        d_dict["createdDateTime"] = datetime.datetime.now()
        # //convert to dict(data)
        coll.insert_one(d_dict)
        return "successfully inserted"
    else:
        return "Telegram group with the given name not created or the AI bot is never introduce in group."

def b_get_camera_credentials(email: str, password: str):
    # database
    db = client["UUAABBCC"]
    coll = db["accountInfo"]
    response = coll.find_one(
        {"cEmail": email, "cPassword": password, "isActive": True}, {"_id": 0})
    return response


@router.post("/setup_registration")
async def setup_registration(data: CameraInfo):
    # send the data to mongodb
    res=await b_setup_registration(data)
    return {"status": res}


@router.get("/get_camera_credentials")
async def get_camera_credentials(email: str, password: str):
    # send the data to mongodb
    res = b_get_camera_credentials(email, password)
    return res


# @router.get("/get_tele_channel_id")
async def get_tele_channel_id(telegram_group_name: str):
    res = 0
    api_url = TELEGRAM_BOT_URL
    try:
        # Send a GET request to the API
        response = requests.get(api_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            data = data.get("result")
            # Process the data
            for item in data:
                try:
                    if item.get("message").get("chat").get("title") == telegram_group_name:
                        res = item.get("message").get("chat").get("id")  # Return the channel id
                        break
                except:
                    print("dictionary error")
        else:
            # Print an error message if the request was not successful
            print(f'Error: {response.status_code}')
    except Exception as e:
        # Handle any exceptions that may occur during the request
        print(f'An error occurred: {e}')
    return res
