import os
import time
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")
DB_NAME = "rag_playbook"
COLLECTION_NAME = "naive_rag"
INDEX_NAME = "naive"

def create_vector_index():
    url = MONGO_DB_URL
    if not url:
        print("Error: MONGO_DB_URL environment variable is not set.")
        print("Please check your .env file.")
        return

    print(f"Connecting to MongoDB at {url}...")
    try:
        client = MongoClient(url)
        # Verify connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return

    db = client[DB_NAME]
    # Ensure collection exists
    if COLLECTION_NAME not in db.list_collection_names():
        print(f"Collection '{COLLECTION_NAME}' does not exist. Please run ingestion first.")
        return
    
    collection = db[COLLECTION_NAME]

    # Atlas Vector Search Index definition
    index_definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 1536,
                "similarity": "cosine"
            }
        ]
    }

    print(f"Checking for existing index '{INDEX_NAME}'...")
    
    try:
        existing_indexes = list(collection.list_search_indexes())
        index_exists = any(idx.get("name") == INDEX_NAME for idx in existing_indexes)

        if index_exists:
            print(f"Index '{INDEX_NAME}' already exists.")
            return

        print(f"Creating vector search index '{INDEX_NAME}'...")
        
        # Create Search Index Model
        model = SearchIndexModel(
            definition=index_definition,
            name=INDEX_NAME,
            type="vectorSearch"
        )
        
        result = collection.create_search_index(model=model)
        print(f"Index creation initiated: {result}")

        print("Waiting for index to become active (this may take a moment)...")
        while True:
            # Poll status
            indexes = list(collection.list_search_indexes(INDEX_NAME))
            if not indexes:
                # Should verify if it was created
                time.sleep(1)
                continue
                
            status = indexes[0].get("status") # 'queryable' boolean in some versions, 'status' string in others
            queryable = indexes[0].get("queryable")
            
            if queryable:
                print("[SUCCESS] Index is ACTIVE and queryable.")
                break
            
            print(f"Current status: {status or 'Building'}...")
            time.sleep(2)

    except OperationFailure as e:
        print(f"MongoDB Operation Failed: {e}")
        print("Note: Ensure you are running MongoDB Atlas Local or an Atlas Cluster.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    create_vector_index()
