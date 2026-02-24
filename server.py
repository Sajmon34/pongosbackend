from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import uvicorn

app = FastAPI()

# Database setup
DB_FILE = "gamedata.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Create the users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chip_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            school_class TEXT,
            score INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Allows us to access columns by name
    return conn

# Data Models
class UserCreate(BaseModel):
    chip_id: str
    username: str
    school_class: str

class ScoreUpdate(BaseModel):
    chip_id: str
    score: int

class UsernameUpdate(BaseModel):
    chip_id: str
    new_username: str

# API Endpoints

@app.post("/adduser")
def add_user(user: UserCreate):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (chip_id, username, school_class) VALUES (?, ?, ?)",
            (user.chip_id, user.username, user.school_class)
        )
        conn.commit()
        return {"message": "User added successfully"}
    except sqlite3.IntegrityError as e:
        # Catch errors if chip_id or username already exists
        raise HTTPException(status_code=400, detail="Chip ID or Username already exists.")
    finally:
        conn.close()

@app.get("/getuserinfo/{chip_id}")
def get_user_info(chip_id: str):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE chip_id = ?", (chip_id,)).fetchone()
    conn.close()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)

@app.post("/setscore")
def set_score(data: ScoreUpdate):
    conn = get_db_connection()
    cursor = conn.execute("UPDATE users SET score = ? WHERE chip_id = ?", (data.score, data.chip_id))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Score updated"}

@app.get("/getscore/{chip_id}")
def get_score(chip_id: str):
    conn = get_db_connection()
    user = conn.execute("SELECT score FROM users WHERE chip_id = ?", (chip_id,)).fetchone()
    conn.close()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"score": user["score"]}

@app.post("/changeusername")
def change_username(data: UsernameUpdate):
    conn = get_db_connection()
    try:
        cursor = conn.execute("UPDATE users SET username = ? WHERE chip_id = ?", (data.new_username, data.chip_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "Username updated"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already taken.")
    finally:
        conn.close()

if __name__ == "__main__":
    # Runs the server on port 8000, accessible from other computers on the local network
    uvicorn.run(app, host="0.0.0.0", port=8000)