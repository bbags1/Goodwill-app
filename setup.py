import os
import shutil
import sqlite3
import sys
import subprocess

def check_python_version():
    """Check if Python version is 3.6 or higher."""
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required.")
        sys.exit(1)
    print("✓ Python version check passed")

def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Python dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("Error: Failed to install Python dependencies.")
        sys.exit(1)

def setup_env_files():
    """Set up environment files."""
    # Backend .env file
    if not os.path.exists("backend/.env"):
        shutil.copy("backend/.env.template", "backend/.env")
        print("✓ Created backend/.env file (please update with your API keys)")
    else:
        print("✓ backend/.env file already exists")
    
    # Frontend .env file
    if not os.path.exists("frontend/.env"):
        shutil.copy("frontend/.env.template", "frontend/.env")
        print("✓ Created frontend/.env file")
    else:
        print("✓ frontend/.env file already exists")

def create_database():
    """Create the SQLite database and tables."""
    # Create data directory if it doesn't exist
    os.makedirs("backend/data", exist_ok=True)
    
    db_path = os.path.join("backend", "data", "gw_data.db")
    
    # Update the DB_PATH in relevant files
    update_db_path(db_path)
    
    # Create database and tables
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create items table
    c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id TEXT PRIMARY KEY,
        search_term TEXT,
        seller_name TEXT,
        product_name TEXT,
        price REAL,
        ebay_price REAL,
        auction_end_time TEXT,
        image_url BLOB,
        shipping_price REAL,
        bids INTEGER,
        seller_id TEXT
    )
    ''')
    
    # Create settings table
    c.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        location TEXT,
        margin_threshold INTEGER,
        notification_email TEXT,
        notification_phone TEXT,
        notification_type TEXT,
        update_frequency TEXT
    )
    ''')
    
    # Create favorites table
    c.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY,
        item_id TEXT,
        date_added TEXT
    )
    ''')
    
    # Create promising table
    c.execute('''
    CREATE TABLE IF NOT EXISTS promising (
        id INTEGER PRIMARY KEY,
        item_id TEXT,
        date_added TEXT
    )
    ''')
    
    # Insert default settings
    c.execute("SELECT COUNT(*) FROM settings")
    if c.fetchone()[0] == 0:
        c.execute('''
        INSERT INTO settings (location, margin_threshold, notification_email, notification_phone, notification_type, update_frequency)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', ('198', 50, '', '', 'email', 'daily'))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database created at {db_path}")

def update_db_path(db_path):
    """Update the DB_PATH variable in Python files."""
    abs_path = os.path.abspath(db_path)
    escaped_path = abs_path.replace('\\', '\\\\')
    
    files_to_update = [
        "backend/app.py",
        "backend/notifications.py",
        "backend/scheduler.py",
        "backend/gemini.py",
        "backend/get_products.py",
        "backend/remove_old.py"
    ]
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
            
            # Replace the DB_PATH line
            if "DB_PATH = " in content:
                content = content.replace(
                    "DB_PATH = r'C:\\Users\\brody\\OneDrive\\Documents\\Copilot\\Goodwill\\backend\\data\\gw_data.db'", 
                    f"DB_PATH = r'{escaped_path}'"
                )
                
                with open(file_path, 'w') as file:
                    file.write(content)
    
    print("✓ Updated database paths in Python files")

def main():
    """Main setup function."""
    print("=== Goodwill Auction Analysis Tool Setup ===")
    
    check_python_version()
    install_dependencies()
    setup_env_files()
    create_database()
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Update backend/.env with your API keys")
    print("2. Start the backend server: cd backend && python app.py")
    print("3. Install frontend dependencies: cd frontend && npm install")
    print("4. Start the frontend server: cd frontend && npm start")
    print("5. (Optional) Set up automatic updates: cd backend && python scheduler.py")

if __name__ == "__main__":
    main() 