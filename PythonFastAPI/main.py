from fastapi import FastAPI
import uvicorn
from bson.objectid import ObjectId
from interface.interfaces import router as api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(debug=True)

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

app.include_router(api_router)

if __name__ == '__main__':
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=8000,
                reload=True)
