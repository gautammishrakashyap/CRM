from typing import Callable
from contextlib import contextmanager
from fastapi import FastAPI
from loguru import logger
from pymongo import MongoClient
from pymongo.database import Database
from app.core.config import (
    MONGODB_URL, MONGODB_MAX_CONNECTIONS_COUNT, MONGODB_MIN_CONNECTIONS_COUNT,
    MONGO_DATABASE
)


class MongoDB:
    """
    MongoDB class to hold a single MongoClient instance for the application.
    """
    client: MongoClient = None

# Create a global MongoDB instance
mongo_db = MongoDB()

def mongodb_startup(app: FastAPI) -> None:
    """
    Establishes a connection to the MongoDB database on application startup.

    Args:
        app (FastAPI): The FastAPI application instance.

    This function sets the MongoDB client instance in the app state, allowing 
    other parts of the application to access the MongoDB connection.
    """
    logger.info('connect to the MongoDB...')
    # Initialize MongoDB client with connection pooling
    mongo_client = MongoClient(
        MONGODB_URL,
        MaxPoolSize = MONGODB_MAX_CONNECTIONS_COUNT,
        MinPoolSize = MONGODB_MIN_CONNECTIONS_COUNT,
    )
    mongo_db.client = mongo_client
    app.state.mongo_client = mongo_client
    logger.info('MongoDB connection succeeded! ')
    
    # Initialize authorization system
    try:
        from app.core.init_auth import initialize_auth_system
        logger.info('Initializing authorization system...')
        result = initialize_auth_system(mongo_client)
        logger.info(f'Authorization system initialized: {result["status"]}')
    except Exception as e:
        logger.error(f'Failed to initialize authorization system: {str(e)}')

def mongodb_shutdown(app: FastAPI) -> None:
    """
    Closes the MongoDB connection on application shutdown.

    Args:
        app (FastAPI): The FastAPI application instance.

    Ensures that the MongoDB connection is gracefully closed when the application stops.
    """
    logger.info('Closing the MongoDB connection...')
    app.state.mongo_client.close()
    logger.info('MondoDB connection closed! ')


def create_start_app_handler(app: FastAPI) -> Callable:
    """
    Creates an application startup handler that connects to MongoDB.

    Args:
        app (FastAPI): The FastAPI application instance.

    Returns:
        Callable: A function that starts the MongoDB connection on application startup.
    """
    def start_app() -> None:
        mongodb_startup(app)
    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable:
    """
    Creates an application shutdown handler that disconnects from MongoDB.

    Args:
        app (FastAPI): The FastAPI application instance.

    Returns:
        Callable: A function that stops the MongoDB connection on application shutdown.
    """
    @logger.catch
    def stop_app() -> None:
        mongodb_shutdown(app)
    return stop_app

@contextmanager
def get_mongodb():
    """
    Context manager to get a temporary MongoDB client connection.

    This method creates a MongoDB client for a specific operation, yielding
    the connection, and ensuring it is properly closed after use.

    Yields:
        db: The MongoDB database instance for use during the context.
    """
    try:
        # Connect to MongoDB and get the database instance
        with MongoClient() as client:
            db = client["clean-database"]
            yield db
    except Exception as e:
        # Log the error and re-raise the exception
        print(f'Error: {e}')
        raise


def get_database() -> Database:
    """
    Get MongoDB database instance from the global client.
    
    Returns:
        Database: The MongoDB database instance.
    """
    if mongo_db.client is None:
        # Initialize client if not already done
        mongo_db.client = MongoClient(
            MONGODB_URL,
            MaxPoolSize=MONGODB_MAX_CONNECTIONS_COUNT,
            MinPoolSize=MONGODB_MIN_CONNECTIONS_COUNT,
        )
    
    return mongo_db.client[MONGO_DATABASE]