from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
# Allow your frontend origin here
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # React default dev server
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # allow your frontend URLs
    allow_credentials=False,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc)
    allow_headers=["*"],  # Allow all headers
)

# Hardcoded credentials (for testing only!)
HARDCODED_USERNAME = "a"
HARDCODED_PASSWORD = "a"

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    if request.username == HARDCODED_USERNAME and request.password == HARDCODED_PASSWORD:
        return {"message": "Login successful!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")
