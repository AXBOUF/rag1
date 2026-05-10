import sqlite3

DB_PATH = '/home/mun/ragt1/version3/users.db'

def list_users():
    """List all users in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, created_at FROM users;")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        print("\n=== Users in Database ===")
        for row in rows:
            print(f"ID: {row[0]}, Username: {row[1]}, Role: {row[2]}, Created: {row[3]}")
    else:
        print("No users found.")

def clear_users():
    """Clear all users from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users;")
    conn.commit()
    conn.close()
    print("✓ All users cleared from database.")

def create_admin(email: str, password: str):
    """Create an admin user with email."""
    from auth import register_user
    success, message = register_user(email, password, "admin")
    if success:
        print(f"✓ Admin user created: {email}")
    else:
        print(f"✗ Failed: {message}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "clear":
            confirm = input("⚠️  Clear all users? (yes/no): ")
            if confirm.lower() == "yes":
                clear_users()
            else:
                print("Cancelled.")
        elif sys.argv[1] == "add":
            if len(sys.argv) < 4:
                print("Usage: python list.py add <email> <password>")
                print("Example: python list.py add admin@gmail.com password123")
            else:
                email = sys.argv[2]
                password = sys.argv[3]
                create_admin(email, password)
        else:
            print("Unknown command")
    else:
        list_users()