from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from auth import user_manager  # Make sure auth.py is in the same folder or adjust import
from report import router as report_router



app = FastAPI()
app.include_router(report_router)

# CORS settings – allow frontend connections
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------

class LoginRequest(BaseModel):
    username: str
    password: str

# ---------- Dependencies ----------

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "").strip()
    user = user_manager.validate_session(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    return user

# ---------- Routes ----------

@app.post("/login")
async def login(request: LoginRequest):
    user = user_manager.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = user_manager.create_session(user["id"])
    if not token:
        raise HTTPException(status_code=500, detail="Failed to create session")

    return {
        
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"]
    }

@app.post("/logout")
async def logout(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "").strip()
    success = user_manager.invalidate_session(token)

    if not success:
        raise HTTPException(status_code=400, detail="Invalid session token")

    return {"message": "Successfully logged out"}

@app.get("/profile")
async def profile(current_user: dict = Depends(get_current_user)):
    return {
        "message": f"Welcome back, {current_user['username']}!",
        "username": current_user["username"],
        "role": current_user["role"]
    }
