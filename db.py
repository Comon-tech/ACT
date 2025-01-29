from pymongo import MongoClient
import dotenv  # type: ignore
import os  # type: ignore
# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi

# Load environment variables
dotenv.load_dotenv()

# uri = "mongodb+srv://comon:<db_password>@cluster0.s3gxs.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
uri = os.getenv("MONGO_URI")

# Create a new client and connect to the server
client = MongoClient(uri)

# Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)

db = client["tact_bot"] 
user_collection = db["users"]
channel_collection = db["channels"]
message_collection = db["messages"]
store_collection = db["store"]
chat_collection = db["chats"]


# Add new items
# items = [
#     {"item_name": "🎖 Special Badge", "item_price": 250, "description": "A badge of honor for extraordinary achievements!"},
#     {"item_name": "🎩 Fancy Hat", "item_price": 500, "description": "Look dashing and make a statement with this classy hat!"},
#     {"item_name": "🦸 Hero Cape", "item_price": 750, "description": "Become the hero you were born to be with this flowing cape."},
#     {"item_name": "🕶 Stylish Sunglasses", "item_price": 300, "description": "Block out the haters and the sun with these sleek shades."},
#     {"item_name": "📜 Scroll of Wisdom", "item_price": 600, "description": "Unlock ancient secrets and knowledge beyond imagination."},
#     {"item_name": "🍔 Burger of Power", "item_price": 150, "description": "A delicious boost to your strength and energy!"},
#     {"item_name": "🛡 Shield of Protection", "item_price": 1000, "description": "Defend yourself against any challenge with this sturdy shield."},
#     {"item_name": "⚔ Sword of Destiny", "item_price": 1200, "description": "Wield the blade of legends to carve your path to glory."},
#     {"item_name": "🐲 Mini Dragon Pet", "item_price": 2000, "description": "A loyal, fire-breathing companion to guard your treasures."},
#     {"item_name": "💎 Rare Gem", "item_price": 800, "description": "A dazzling jewel that radiates wealth and power."},
#     {"item_name": "✨ Magic Wand", "item_price": 900, "description": "Cast enchanting spells and dazzle your friends."},
#     {"item_name": "🎮 Gamer Setup", "item_price": 2500, "description": "Level up your gaming experience with this ultimate setup."},
#     {"item_name": "🚗 Toy Car", "item_price": 350, "description": "A miniature speedster for endless fun."},
#     {"item_name": "🏰 Castle Blueprint", "item_price": 3000, "description": "Build your dream fortress and rule the land!"},
#     {"item_name": "🛶 Kayak Adventure", "item_price": 750, "description": "Set sail on thrilling waters with this adventurous kayak."},
#     {"item_name": "📦 Mystery Box", "item_price": 500, "description": "What's inside? Only the bravest find out!"},
#     {"item_name": "🌟 Wish Token", "item_price": 1000, "description": "Make a wish and let the magic unfold."},
#     {"item_name": "🐱 Cat Companion", "item_price": 1100, "description": "A fluffy friend to keep you company on your journeys."},
#     {"item_name": "🦄 Unicorn Horn", "item_price": 1800, "description": "Harness the mythical power of the legendary unicorn."},
#     {"item_name": "🚀 Rocket Model", "item_price": 1400, "description": "Launch your dreams to the stars with this intricate rocket."},
# ]


# store_collection.insert_many(items)

# print("Fun items added to the store!")



