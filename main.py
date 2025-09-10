from fastapi import FastAPI, HTTPException, Form, File, UploadFile, status
from pydantic import BaseModel
from db import advert_collection
from bson.objectid import ObjectId
from typing import Annotated
from utils import replace_mongo_id
import cloudinary
import cloudinary.uploader


cloudinary.config(
    cloud_name = "dyhqmkyfc",
    api_key = "617624249245792",
    api_secret = "cAhgM5MehvpHZu6wgW23h63n9WM"
)


app = FastAPI()

class NewAdvert(BaseModel):
    title: str
    description: str
    price: float
    flyer: str

# creates an endpoint to the homepage
@app.get("/")
def root():
    return{"Message":"Welcome to our Advertisement Management API"}

# allows vendors to create a new advert.
@app.post("/advert")
def new_advert(
    title: Annotated[str, Form()], 
    description: Annotated[str, Form()], 
    price: Annotated[float, Form()],
    flyer:Annotated[UploadFile, File()]):

    # upload flyer to cloudinary to get a url
    upload_advert = cloudinary.uploader.upload(flyer.file)
    advert_collection.insert_one({
        "title": title,
        "description": description,
        "price": price,
        "flyer": upload_advert["secure_url"]
    })
    return{"message": "Advert Sucessfully created"}

# allows vendors to view all adverts.
@app.get("/adverts")
def all_adverts(title= "", description="", limit: int = 10, skip: int = 0):
    advert = advert_collection.find().skip(skip).limit(limit)
    return {"data": list(map(replace_mongo_id, advert))}

# allows vendors to view a specific advert’s details
@app.get("/advert_details/{title}")
def advert_details(title:str):
    adverts = advert_collection.find_one({"title":title})
    if not adverts:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Sorry advert not found😞")
    return {"data": [replace_mongo_id(adverts)]}

# allows vendors to edit an advert
@app.put("/edit_advert/{title}")
def advert_edit(
    title: str,
    new_title: Annotated[str, Form()],
    description: Annotated[str, Form()], 
    price: Annotated[float, Form()],
    flyer:Annotated[UploadFile, File()]):
    adverts = advert_collection.find_one({"title":title})
    if not adverts:
        raise HTTPException(status_code=404, detail="Sorry advert not found😞")
    
    uploald_advert = cloudinary.uploader.upload(flyer.file)
    advert_collection.replace_one({"title": title}, 
    {
        "Title": new_title,
        "Description": description,
        "price": price,
        "Flyer": uploald_advert["secure_url"]
    })
    return{"message": "You have successfully updated your Advert✅"}

# allows vendors to remove an advert
@app.delete("/adverts/{title}")
def delete_advert(title: str):
    adverts = advert_collection.find_one({"title":title})
    if not adverts:
        raise HTTPException(status_code=404, detail="Sorry advert not found to be deleted😞")
    advert_collection.delete_one({"title":title})
    return{"message": "Advert successfully deleted!"}
