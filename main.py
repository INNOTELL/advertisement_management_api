from datetime import datetime, timedelta, timezone
import os
from bson import ObjectId
from fastapi import FastAPI, HTTPException,Query,Form, File, UploadFile, status,Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
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
SECRET_KEY = os.getenv("JWT_SECRET_KEY","secret_key")
ALGORITHM = "HS256"

oauth2_scheme = HTTPBearer()


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
    },
    {
        "name": "🛒Vendor Dashboard"
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
    user = "User"


# creates an endpoint to the homepage
@app.get("/", tags=["Home"])
def root():
    return{"Message":"Welcome to our Advertisement Management API"}
# Extract current user from token
def get_current_user(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"_id": user_id, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# register a new user
@app.post("/SignUp", tags=["Sign Up/Login Page"])
def signup(
    username: Annotated[str, Form(min_length=6, max_length=12)],
    email: Annotated[EmailStr, Form],
    password: Annotated[str, Form(min_length=8)],
    role: RoleEnum = RoleEnum.user 
 
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
    email: Annotated[EmailStr, Form],
    password: Annotated[str, Form]
):
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist")

    # Compare their password
    stored_password = user["password"].encode("utf-8")
    if not bcrypt.checkpw(password.encode("utf-8"), stored_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    # Generate access token
    payload = {
        "sub": str(user["_id"]),
        "role": user["role"],
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=362)
    }
    encoded_jwt = jwt.encode(payload,SECRET_KEY, algorithm=ALGORITHM)

    return {
        "message": f"Welcome back, {user['username']}!",
        "access_token": encoded_jwt
    }
   
# allows vendors to create a new advert.
@app.post("/advert", tags=["🛒Vendor Dashboard"])
def new_advert(
    title: Annotated[str, Form()], 
    description: Annotated[str, Form()], 
    price: Annotated[float, Form()],
    category: CategoryEnum,
    location: LocationEnum,
    image: Annotated[UploadFile, File()],
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Vendor":
        raise HTTPException(status_code=403, detail="Only vendors can create adverts")

    upload_advert = cloudinary.uploader.upload(image.file)
    advert_collection.insert_one({
        "owner_id": current_user["_id"],  # vendor id
        "title": title,
        "description": description,
        "price": price,
        "category": category.value,
        "location": location.value,
        "image": upload_advert["secure_url"]
    })
    return {"message": "Advert successfully created ✅"}

# generate a preview of ad before publishing
@app.post("/ads_preview", tags=["🛒Vendor Dashboard"])
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

# allows vendors to edit an advert
@app.put("/edit_advert/{id}", tags=["🛒Vendor Dashboard"])
def advert_edit(
    id: str,
    new_title: Annotated[str, Form()],
    description: Annotated[str, Form()], 
    price: Annotated[float, Form()],
    category: Annotated[str, Form()],
    location: LocationEnum,
    image: Annotated[UploadFile, File()],
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "Vendor":
        raise HTTPException(status_code=403, detail="Only vendors can edit adverts")

    ad = advert_collection.find_one({"_id": ObjectId(id)})
    if not ad:
        raise HTTPException(status_code=404, detail="Advert not found")

    if ad["owner_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="You can only edit your own adverts")

    upload_advert = cloudinary.uploader.upload(image.file)
    advert_collection.update_one({"_id": ObjectId(id)}, 
        { "$set": {
            "title": new_title,
            "description": description,
            "price": price,
            "category": category,
            "location": location.value,
            "image": upload_advert["secure_url"]
        }}
    )
    return {"message": "You have successfully updated your Advert ✅"}

# allows vendors to remove an advert
@app.delete("/adverts/{id}", tags=["🛒Vendor Dashboard"])
def delete_advert(id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Vendor":
        raise HTTPException(status_code=403, detail="Only vendors can delete adverts")

    advert = advert_collection.find_one({"_id": ObjectId(id)})
    if not advert:
        raise HTTPException(status_code=404, detail="Advert not found")

    if advert["owner_id"] != current_user["_id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own adverts")

    advert_collection.delete_one({"_id": ObjectId(id)})
    return {"message": "Advert successfully deleted ✅"}

#  Show ads near a user’s location
@app.get("/adverts_nearby/{user_location}", tags=["Manage Advert"])
def get_ads_by_location(user_location: LocationEnum):
    ads = list(advert_collection.find(
        {"location": {"$regex": user_location.value, "$options": "i"}}
    ))
    return {"ads": list(map(replace_mongo_id, ads))}


#  View all ads posted by a specific advertiser
@app.get("/advertisers/{id}", tags=["Manage Advert"])
def advertiser_profile(id: str):
    ads = list(advert_collection.find({"advertiser_id": id}))
    if not ads:
        raise HTTPException(status_code=404, detail="No ads found for this advertiser")
    return {"ads": list(map(replace_mongo_id, ads))}

#  Suggest ads based on the user’s history, interests, or location
@app.get("/recommendations/{ads}", tags=["Manage Advert"])
def recommendation(ads: str):
    recs = list(advert_collection.find(
        {"category": {"$regex": ads, "$options": "i"}}
    ).limit(5))
    return {"recommended": list(map(replace_mongo_id, recs))}

#  Find ads by category, location, or keyword
@app.get("/ads/search", tags=["Manage Advert"])
def search_filtering(
    category: Optional[str] = None,
    location: Optional[str] = None,
    keyword: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    query = {}

    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if keyword:
        query["title"] = {"$regex": keyword, "$options": "i"}
    if min_price is not None and max_price is not None:
        query["price"] = {"$gte": min_price, "$lte": max_price}
    elif min_price is not None:
        query["price"] = {"$gte": min_price}
    elif max_price is not None:
        query["price"] = {"$lte": max_price}

    ads = list(advert_collection.find(query))
    return {"ads": list(map(replace_mongo_id, ads))}

# allows vendors to view all adverts
@app.get("/adverts", tags=["Manage Advert"])
def all_adverts(limit: int = 10, skip: int = 0):
    adverts = advert_collection.find().skip(skip).limit(limit)
    return {"data": list(map(replace_mongo_id, adverts))}

# allows vendors to view a specific advert’s details
@app.get("/advert_details/{id}", tags=["Manage Advert"])
def advert_details(id: str):
    try:
        advert = advert_collection.find_one({"_id": ObjectId(id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid advert ID format")
    
    if not advert:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Sorry advert not found😞")

    # Get related adverts from the same category (excluding this advert)
    related_ads = list(advert_collection.find({
        "category": advert["category"],
        "_id": {"$ne": advert["_id"]}
    }).limit(5))

    return {
        "data": replace_mongo_id(advert),
        "related": list(map(replace_mongo_id, related_ads))
    }

# Report an inappropriate or scam ad
@app.post("/adverts/{id}/report", tags=["Report An Advert❌"])
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

