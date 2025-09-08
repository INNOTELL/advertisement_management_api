from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return{"Message":"Welcome to our Advertisement Management API"}