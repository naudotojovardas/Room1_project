# main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from database import init_db
from todo import router as todo_router
from auth import add_auth_routes
from fastapi.middleware.cors import CORSMiddleware
# Initialize the database
init_db()

app = FastAPI()

# Fix the CORS issue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You might want to restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(todo_router, prefix="/todos", tags=["todos"])

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



if __name__ == "__main__":
    init_db()  # Only run this when starting the main application server
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)

    print("Initializing database...")