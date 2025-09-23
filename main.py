from bson import ObjectId
from fastapi import FastAPI, HTTPException,Query,Form, File, UploadFile, status
from pydantic import BaseModel, EmailStr
from db import advert_collection
from db import users_collection
from bson.errors import InvalidId
from typing import Annotated, Optional
from enum import Enum
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
        "name": "Manage Advert",
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

class CategoryEnum(str, Enum):
    babies = "Babies & Kids"
    electronics = "Electronics"
    fashion = "Fashion"
    cars = "Cars"
    real_estate = "Real Estate"
    jobs = "Jobs"
    home = "Home,Furniture & Appliances"
    beauty = "Beauty & Personal Care"
    food = "Food & Agriculture"

class LocationEnum(str, Enum):
    accra = "Greater Accra"
    central = "Central Region"
    ashanti = "Ashanti Region"
    brong = "Brong Ahafo Region"
    eastern= "Eastern Region"
    northern = "Northern Region"
    upper_east = "Upper East Region"
    upper_west = "Upper West Region"
    volta = "Volta Region"
    western = "Western Region"

class NewAdvert(BaseModel):
    title: str 
    description: str
    price: float
    category: CategoryEnum
    image: str
    location: LocationEnum


class AdPreview(BaseModel):
    title: str
    description: str
    price: float
    category: CategoryEnum
    image: str
    location: LocationEnum

class Report(BaseModel):
    reason: str

class RoleEnum(str, Enum):
    vendor = "Vendor"
    buyer = "Buyer"


# creates an endpoint to the homepage
@app.get("/", tags=["Home"])
def root():
    return{"Message":"Welcome to our Advertisement Management API"}

# register a new user
@app.post("/SignUp", tags=["Sign Up/Login Page"])
def signup(
    username: Annotated[str, Form(min_length=6, max_length=12)],
    email: Annotated[EmailStr, Form],
    password: Annotated[str, Form(min_length=8)],
    role: RoleEnum = RoleEnum.buyer 
 
):
    if users_collection.find_one({"email": email}):
        raise HTTPException(status.HTTP_409_CONFLICT, "User already exists!")

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    result = users_collection.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password,
        "role": role.value
    })
    return {
        "message": "You've been registered successfully!",
        "user_id": str(result.inserted_id),
        "role": role.value
    }


@app.post("/Login", tags=["Sign Up/Login Page"])
def login(
    email: Annotated[EmailStr,Form],
    password: Annotated[str, Form]):
    user = users_collection.find_one({"email":email})
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND,"Wrong email/password!!!")
    stored_hash = user["password"].encode("utf-8")   
    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Wrong email or password!!!")
    return {"message": f"Welcome back, {user['username']}!"}

   
# allows vendors to create a new advert.
@app.post("/advert", tags=["Manage Advert"])
def new_advert(
    advertiser_id: Annotated[str,Form()],
    title: Annotated[str, Form()], 
    description: Annotated[str, Form()], 
    price: Annotated[float, Form()],
    category: CategoryEnum,
    location: LocationEnum,
    image:Annotated[UploadFile, File()]):

    # upload flyer to cloudinary to get a url
    upload_advert = cloudinary.uploader.upload(image.file)
    advert_collection.insert_one({
        "advertiser_id":advertiser_id,
        "title": title,
        "description": description,
        "price": price,
        "category": category.value,
        "location": location.value,
        "image": upload_advert["secure_url"]

    })
    return{"message": "Advert Sucessfully created✅"}

# generate a preview of ad before publishing
@app.post("/ads_preview")
def preview_advert(ad: AdPreview):
#  return the ad back to the user
 return {
            "preview": {
            "title": ad.title,
            "description": ad.description,
            "price": ad.price,
            "category": ad.category,
            "image": ad.image,
            "location": ad.location
        }
    }
#  Show ads near a user’s location
@app.get("/adverts_nearby/{user_location}")
def get_ads_by_location(user_location: LocationEnum):
    ads = list(advert_collection.find(
        {"location": {"$regex": user_location.value, "$options": "i"}}
    ))
    return {"ads": list(map(replace_mongo_id, ads))}


#  View all ads posted by a specific advertiser
@app.get("/advertisers/{id}")
def advertiser_profile(id: str):
    ads = list(advert_collection.find({"advertiser_id": id}))
    if not ads:
        raise HTTPException(status_code=404, detail="No ads found for this advertiser")
    return {"ads": list(map(replace_mongo_id, ads))}

# Report an inappropriate or scam ad
@app.post("/adverts/{id}/report")
def report(id: str, report: Report):
    result = advert_collection.update_one(
        {"_id": ObjectId(id)},
        {"$push": {"reports": {"reason": report.reason}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ad not found")
    return {
        "message": f"Ad {id} reported successfully. We will review it.",
        "reason": report.reason
    }

#  Suggest ads based on the user’s history, interests, or location
@app.get("/recommendations/{ads}")
def recommendation(ads: str):
    recs = list(advert_collection.find(
        {"category": {"$regex": ads, "$options": "i"}}
    ).limit(5))
    return {"recommended": list(map(replace_mongo_id, recs))}

#  Find ads by category, location, or keyword
@app.get("/ads/search")
def search_filtering(
    category: Optional[str] = None,
    location: Optional[str] = None,
    keyword: Optional[str] = None
):
    query = {}

    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if keyword:
        query["title"] = {"$regex": keyword, "$options": "i"}

    ads = list(advert_collection.find(query))
    return {"ads": list(map(replace_mongo_id, ads))}

# allows vendors to view all adverts
@app.get("/adverts", tags=["Manage Advert"])
def all_adverts(limit: int = 10, skip: int = 0):
    adverts = advert_collection.find().skip(skip).limit(limit)
    return {"data": list(map(replace_mongo_id, adverts))}

# allows vendors to view a specific advert’s details
@app.get("/advert_details/{id}", tags=["Manage Advert"])
def advert_details(id:str):
    try:
        adverts = advert_collection.find_one({"_id": ObjectId(id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid advert ID format")
    adverts = advert_collection.find_one({"_id": ObjectId(id)})
    if not adverts:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Sorry advert not found😞")
    return {"data":replace_mongo_id(adverts)}
    
# allows vendors to edit an advert
@app.put("/edit_advert/{id}", tags=["Manage Advert"])
def advert_edit(
    id: str,
    title: str,
    new_title: Annotated[str, Form()],
    description: Annotated[str, Form()], 
    price: Annotated[float, Form()],
    category: Annotated[str, Form()],
    location: LocationEnum,
    image:Annotated[UploadFile, File()]):

    ad = advert_collection.find_one({"_id":ObjectId(id)})
    if not ad:
        raise HTTPException(status_code=404, detail="Sorry advert not found😞")
    uploald_advert = cloudinary.uploader.upload(image.file)

    advert_collection.update_one({"_id":ObjectId(id)}, 
    { "$set": {
        "title": new_title,
        "description": description,
        "price": price,
        "category": category,
        "location": location.value,
        "image": uploald_advert["secure_url"]
    }}
    )
    return{"message": "You have successfully updated your Advert✅"}

# allows vendors to remove an advert
@app.delete("/adverts/{id}", tags=["Manage Advert"])
def delete_advert(id: str):
    try:
        advert_obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid advert ID")

    advert = advert_collection.find_one({"_id":ObjectId(id)})
    if not advert:
        raise HTTPException(status_code=404, detail="Sorry advert not found to be deleted😞")
    advert_collection.delete_one({"_id":ObjectId(id)})
    return{"message": "Advert successfully deleted!"}
  