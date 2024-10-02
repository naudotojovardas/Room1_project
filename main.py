# main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from database import init_db
from todo import router as todo_router
from auth import add_auth_routes

# Initialize the database
init_db()

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTMLResponse(content=open("static/index.html").read())

# Favicon endpoint
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return ""

# Add authentication routes
add_auth_routes(app)

# Include the TODO routes with a prefix
app.include_router(todo_router, prefix="/todos")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
