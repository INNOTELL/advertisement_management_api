from fastapi import FastAPI, HTTPException, Form, File, UploadFile, status
from pydantic import BaseModel
from db import advert_collection
# from bson.objectid import ObjectId
from typing import Annotated
from utils import replace_mongo_id
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os


load_dotenv()

tags_metadata = [
    {
        "name": "Home",
        "description": "welcome to our our Advertisement Management API"
    },
    {
        "name": "Advert",
        "description": "ads"
    }

]

cloudinary.config(
    cloud_name = os.getenv("CLOUD_NAME"),
    api_key = os.getenv("API_KEY"),
    api_secret = os.getenv("API_SECRET")
)

tags_metadata = [
    {
        "name": "Home",
        "description": "welcome to our our Advertisement Management API"
    },
    {
        "name": "Advert",
        "description": "ads"
    }]


app = FastAPI()

class NewAdvert(BaseModel):
    Title: str
    Description: str
    Price: float
    Category: str
# creates a list to store posted ads

# creates an endpoint to the homepage
@app.get("/", tags=["Home"])
def root():
    return{"Message":"Welcome to our Advertisement Management API"}

# allows vendors to create a new advert.
@app.post("/advert", tags=["Advert"])
def new_advert(
    Title: Annotated[str, Form()], 
    Description: Annotated[str, Form()], 
    Price: Annotated[float, Form()],
    Category: Annotated[str, Form()],
    Image:Annotated[UploadFile, File()]):

    # upload flyer to cloudinary to get a url
    upload_advert = cloudinary.uploader.upload(Image.file)

    advert_collection.insert_one({
        "title": Title,
        "Description": Description,
        "price": Price,
        "category": Category,
        "Image": upload_advert["secure_url"]
    })
    return{"message": "Sucessful"}

# allows vendors to view all adverts.
@app.get("/adverts", tags=["Advert"])
def all_adverts(Title= "", limit = 10, skip = 0):
    advert = advert_collection.find(limit = int(limit), skip = int(skip)).to_list()
    return {"data": list(map(replace_mongo_id, advert))}


# allows vendors to view a specific advert’s details
@app.get("/advert_details/{Title}", tags=["Advert"])
def advert_details(Title:str):
    ads = advert_collection.find_one({"title":Title})
    if not ads:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Sorry advert not found😞")
    return {"data": [replace_mongo_id(ads)]}

    
# allows vendors to edit an advert
@app.put("/edit_advert/{title}", tags=["Advert"])
def advert_edit(
    Title: Annotated[str, Form()], 
    Description: Annotated[str, Form()], 
    Price: Annotated[float, Form()],
    Category: Annotated[str, Form()],
    flyer:Annotated[UploadFile, File()]):
    adverts = advert_collection.find_one({"title":Title})
    if not adverts:
        raise HTTPException(status_code=404, detail="Sorry advert not found😞")
    uploald_advert = cloudinary.uploader.upload(flyer.file)
    advert_collection.replace_one({"title": Title}, replacement= {
        "Title": Title,
        "Description": Description,
        "price": Price,
        "category": Category,
        "Flyer": uploald_advert["secure_url"]
    })
    return{"message": "You have successfully updated your Ad✅"}

# allows vendors to remove an advert
@app.delete("/adverts/{title}", tags=["Advert"])
def delete_advert(Title: str):
    adverts = advert_collection.find_one({"title":Title})
    if not adverts:
        raise HTTPException(status_code=404, detail="Sorry advert not found to be deleted😞")
    advert_collection.delete_one({"title":Title})
    return{"message": "Advert successfully deleted!"}
