from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.getenv("MONGO_URI"))

advertisement_db = mongo_client["advertisement_db"]

advert_collection = advertisement_db["adverts"]

users_collection = advertisement_db["users"]

cart_collection =advertisement_db["cart"]

wishlist_collection = advertisement_db["wishlist"]