from fastapi import FastAPI, HTTPException, Form, File, UploadFile, status
from pydantic import BaseModel
from db import advert_collection
# from bson.objectid import ObjectId
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
    Title: str
    Description: str
    Price: float
    Category: str
# creates a list to store posted ads
# advert = []

# creates an endpoint to the homepage
@app.get("/")
def root():
    return{"Message":"Welcome to our Advertisement Management API"}

# allows vendors to create a new advert.
@app.post("/advert")
def new_advert(
    Title: Annotated[str, Form()], 
    Description: Annotated[str, Form()], 
    Price: Annotated[float, Form()],
    flyer:Annotated[UploadFile, File()]):

    # upload flyer to cloudinary to get a url
    upload_advert = cloudinary.uploader.upload(flyer.file)

    advert_collection.insert_one({
        "title": Title,
        "Description": Description,
        "price": Price,
        "flyer": upload_advert["secure_url"]
    })
    return{"message": "Your advert has been posted sucessfully!"}

# allows vendors to view all adverts.
@app.get("/adverts")
def all_adverts(Title= "", description="", limit = 10, skip = 0):
    advert = advert_collection.find(limit = int(limit), skip = int(skip)).to_list()
    return {"data": list(map(replace_mongo_id, advert))}

# def all_adverts():
#     return{"all_adverts":{advert_collection}}

# allows vendors to view a specific advert’s details
@app.get("/advert_details/{Title}")
def advert_details(Title:str):
    adverts = advert_collection.find_one({"title":Title})
    if not adverts:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Sorry advert not found😞")
    return {"data": [replace_mongo_id(adverts)]}

    # for adverts in advert_collection:
    #     if adverts["Title"] == Title:
    #         return ads
    #     raise HTTPException(status_code=404, detail="Advert not found")
    
# allows vendors to edit an advert
@app.put("/edit_advert/{title}")
def advert_edit(
    Title: Annotated[str, Form()], 
    Description: Annotated[str, Form()], 
    Price: Annotated[float, Form()],
    flyer:Annotated[UploadFile, File()]):
    adverts = advert_collection.find_one({"title":Title})
    if not adverts:
        raise HTTPException(status_code=404, detail="Sorry advert not found😞")
    uploald_advert = cloudinary.uploader.upload(flyer.file)
    advert_collection.replace_one({"title": Title}, replacement= {
        "Title": Title,
        "Description": Description,
        "price": Price,
        "Flyer": uploald_advert["secure_url"]
    })
    return{"message": "You have successfully updated your Add✅"}

# allows vendors to remove an advert
@app.delete("/adverts/{title}")
def delete_advert(Title):
    adverts = advert_collection.find_one({"title":Title})
    if not adverts:
        raise HTTPException(status_code=404, detail="Sorry advert not found to be deleted😞")
    advert_collection.delete_one({"title":Title})
    return{"message": "Advert successfully deleted!"}
