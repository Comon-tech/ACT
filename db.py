from pymongo import MongoClient
import dotenv  # type: ignore
import os  # type: ignore
# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi

# Load environment variables
dotenv.load_dotenv()

# uri = "mongodb+srv://comon:<db_password>@cluster0.s3gxs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
uri = os.getenv("MONGO_URI")

print("uri: ", uri)
# Create a new client and connect to the server
client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


# import os
# import dotenv

# # Load environment variables
# dotenv.load_dotenv()

# # MongoDB setup
# mongo_uri = os.getenv('MONGO_URI')
# client = MongoClient(mongo_uri)
# db = client['matchmakerdb']
