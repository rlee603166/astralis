# src/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from users.router import router as user_router
from search.router import router as search_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(search_router)

@app.get("/")
def root():
    return { "message": "BREAK EVERYTHING" }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

