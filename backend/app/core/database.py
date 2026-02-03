from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None

    def connect(self):
        """Create database connection."""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        print("Connected to MongoDB")

    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            print("Closed MongoDB connection")

    def get_db(self):
        """Get database instance."""
        return self.client.get_database()

db = Database()
