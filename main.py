from fastapi import FastAPI, HTTPException, Form, File, UploadFile, status
from pydantic import BaseModel, EmailStr
from db import advert_collection
from typing import Annotated
from utils import replace_mongo_id
import cloudinary
import cloudinary.uploader
import bcrypt
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
    },
    {
        "name":"Sign Up/Login Page",
        "description":"Sign Up or Login to join a community of vendors"
    }

]

cloudinary.config(
    cloud_name = "dyhqmkyfc",
    api_key = "617624249245792",
    api_secret = "cAhgM5MehvpHZu6wgW23h63n9WM"
)

app = FastAPI(title="Inno_Hub", description="Welcome to Inno Hub🛒,Buy and Sell all your products from the comfort of your home🌏", version="1.0")

class NewAdvert(BaseModel):
    title: str
    description: str
    price: float
    category: str
    image: str

# creates an endpoint to the homepage
@app.get("/", tags=["Home"])
def root():
    return{"Message":"Welcome to our Advertisement Management API"}

# register a new user
@app.post("/Sign up", tags=["Sign Up/Login Page"])
def signup(
    username: Annotated[str,Form()],
    email: Annotated[EmailStr,Form],
    password: Annotated[str, Form(min_length=10)]):

    # Ensure user does not exist
    user_count = advert_collection.count_documents(filter={"email":email})
    if user_count > 0:
      raise HTTPException(status.HTTP_409_CONFLICT,"User already exist!")
# Hash user password   
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
# save users into database
    advert_collection.insert_one({
    "username": username,
    "email": email,
    "password":hashed_password})
    return{"message":"You've been registered sucessfully!"}
   
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
    return{"message": "Advert Sucessfully created✅"}

# allows vendors to view all adverts
@app.get("/adverts", tags=["Advert"])
def all_adverts(title= "", description="", limit: int = 10, skip: int = 0):
    advert = advert_collection.find().skip(skip).limit(limit)
    return {"data": list(map(replace_mongo_id, advert))}

# allows vendors to view a specific advert’s details
@app.get("/advert_details/{id}", tags=["Advert"])
def advert_details(id):
    adverts = advert_collection.find_one({"_id":id})
    if not adverts:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Sorry advert not found😞")
    return {"data": [replace_mongo_id(adverts)]}
    
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
