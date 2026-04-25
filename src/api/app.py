from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")