from app import create_app, db
from app.models.candidate import Candidate

def init_db():
    """Initialize the database"""
    app = create_app()
    with app.app_context():
        # Drop all tables if they exist
        print("Dropping all tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        
        # Verify tables were created
        tables = db.engine.table_names()
        print(f"Created tables: {tables}")
        
        print("Database initialization completed successfully!")

if __name__ == '__main__':
    init_db()
