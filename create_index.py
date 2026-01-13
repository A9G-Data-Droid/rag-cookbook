import time
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

def create_vector_index(mongodb_url, db_name, collection_name, index_name, index_definition):
    """
    Generic function to create a MongoDB Atlas Search Vector Index.
    """
    if not mongodb_url:
        print("Error: MONGO_DB_URL is not provided.")
        return

    print(f"Connecting to MongoDB...")
    try:
        client = MongoClient(mongodb_url)
        # Verify connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB.")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return

    db = client[db_name]
    
    # Ensure collection exists
    if collection_name not in db.list_collection_names():
        print(f"Collection '{collection_name}' does not exist.")
        print("IMPORTANT: You must run the ingestion script for this section first.")
        client.close()
        return 
    
    collection = db[collection_name]

    print(f"Checking for existing index '{index_name}' on '{collection_name}'...")
    
    try:
        existing_indexes = list(collection.list_search_indexes())
        index_exists = any(idx.get("name") == index_name for idx in existing_indexes)

        if index_exists:
            print(f"Index '{index_name}' already exists.")
            return

        print(f"Creating vector search index '{index_name}'...")
        
        model = SearchIndexModel(
            definition=index_definition,
            name=index_name,
            type="vectorSearch"
        )
        
        result = collection.create_search_index(model=model)
        print(f"Index creation initiated: {result}")

        print("Waiting for index to become active (this may take a moment)...")
        while True:
            indexes = list(collection.list_search_indexes(index_name))
            if not indexes:
                time.sleep(1)
                continue
                
            status = indexes[0].get("status")
            queryable = indexes[0].get("queryable")
            
            if queryable:
                print(f"[SUCCESS] Index '{index_name}' is ACTIVE and queryable.")
                break
            
            print(f"Current status: {status or 'Building'}...")
            time.sleep(2)

    except OperationFailure as e:
        print(f"MongoDB Operation Failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()
