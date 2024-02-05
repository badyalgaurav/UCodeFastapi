from fastapi import APIRouter

from interface import i_signup
from interface import i_geocam
'''router information'''
router = APIRouter()
router.include_router(i_signup.router)
router.include_router(i_geocam.router)
