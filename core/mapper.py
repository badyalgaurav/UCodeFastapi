from database.database import sp_call
import traceback

def get_call(query: dict):
    try:
        response = sp_call(query['sp_name'], query["sp_param"])
        message = "MSG_100"
    except:
        message = "MSG_99"
        response = {traceback.format_exc()}
    return {"data": {"o_data": response}, "message": message}