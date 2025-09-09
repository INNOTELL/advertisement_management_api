from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bson.objectid import ObjectId
from typing import Annotated
import cloudinary
import cloudinary.uploader


app = FastAPI()

class NewAdvert(BaseModel):
    Title: str
    Description: str
    Price: float
    Category: str

# creates a list to store posted ads
advert = []

# creates an endpoint to the homepage
@app.get("/")
def root():
    return{"Message":"Welcome to our Advertisement Management API"}

# allows vendors to create a new advert.
@app.post("/post_advert")
def new_advert(new_advert: NewAdvert):
    advert.append(new_advert.model_dump())
    return{"message": "Your advert has been posted sucessfully!"}

# allows vendors to view all adverts.
@app.get("/all_adverts")
def all_adverts():
    return{"all_adverts":advert}

# allows vendors to view a specific advert’s details
@app.get("/advert_details/{Title}")
def advert_details(Title:str):
    for ads in advert:
        if ads["Title"] == Title:
            return ads
        raise HTTPException(status_code=404, detail="Advert not found")
    
# allows vendors to edit an advert
@app.put("/edit_advert/{Title}")
def advert_edit(Title,Description,Price,Category):
    if not ObjectId.is_valid(Title):
         raise HTTPException(status_code=404, detail="Advert not found")
    

# allows vendors to remove an advert
@app.delete("/adverts/{Title}")
def delete(Title):
    if not ObjectId.is_valid(Title):
        raise HTTPException(status_code=404, detail="Advert not found")
    advert.delete_one(filter={"Title": ObjectId(Title)})
    return{"message": "Advert successfully deleted!"}

    


        
        

