from fastapi import FastAPI, HTTPException, Form, File, UploadFile, status
from pydantic import BaseModel
from db import advert_collection
# from bson.objectid import ObjectId
from typing import Annotated
from utils import replace_mongo_id
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv



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
    cloud_name = "dyhqmkyfc",
    api_key = "617624249245792",
    api_secret = "cAhgM5MehvpHZu6wgW23h63n9WM"
)


app = FastAPI()

class NewAdvert(BaseModel):
    title: str
    description: str
    price: float
    category: str
    image: str

# creates a list to store posted ads

# creates an endpoint to the homepage
@app.get("/", tags=["Home"])
def root():
    return{"Message":"Welcome to our Advertisement Management API"}

# allows vendors to create a new advert.
@app.post("/advert", tags=["Advert"])
def new_advert(
    title: Annotated[str, Form()], 
    description: Annotated[str, Form()], 
    price: Annotated[float, Form()],
    category: Annotated[str, Form()],
    image:Annotated[UploadFile, File()]):

    # upload flyer to cloudinary to get a url
    upload_advert = cloudinary.uploader.upload(image.file)
    advert_collection.insert_one({
        "title": title,
        "description": description,
        "price": price,
        "category": category,
        "image": upload_advert["secure_url"]

    })
    return{"message": "Advert Sucessfully created"}

# allows vendors to view all adverts.

@app.get("/adverts", tags=["Advert"])
def all_adverts(title= "", description="", limit: int = 10, skip: int = 0):
    advert = advert_collection.find().skip(skip).limit(limit)
    return {"data": list(map(replace_mongo_id, advert))}

# def all_adverts():
#     return{"all_adverts":{advert_collection}}

# allows vendors to view a specific advert’s details
@app.get("/advert_details/{title}", tags=["Advert"])
def advert_details(title:str):
    adverts = advert_collection.find_one({"title":title})
    if not adverts:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Sorry advert not found😞")
    return {"data": [replace_mongo_id(adverts)]}

    # for adverts in advert_collection:
    #     if adverts["Title"] == Title:
    #         return ads
    #     raise HTTPException(status_code=404, detail="Advert not found")
    
# allows vendors to edit an advert
@app.put("/edit_advert/{title}", tags=["Advert"])
def advert_edit(
    title: str,
    new_title: Annotated[str, Form()],
    description: Annotated[str, Form()], 
    price: Annotated[float, Form()],
    category: Annotated[str, Form()],
    image:Annotated[UploadFile, File()]):

    ad = advert_collection.find_one({"title":title})
    if not ad:
        raise HTTPException(status_code=404, detail="Sorry advert not found😞")
    uploald_advert = cloudinary.uploader.upload(image.file)

    advert_collection.update_one({"title": title}, 
    { "$set": {
        "title": new_title,
        "description": description,
        "price": price,
        "category": category,
        "image": uploald_advert["secure_url"]
    }}
    )
    return{"message": "You have successfully updated your Advert✅"}

# allows vendors to remove an advert
@app.delete("/adverts/{title}", tags=["Advert"])
def delete_advert(title: str):
    advert = advert_collection.find_one({"title": title})

    if not advert:
        raise HTTPException(status_code=404, detail="Sorry advert not found to be deleted😞")
    advert_collection.delete_one({"title": title})
    return{"message": "Advert successfully deleted!"}
