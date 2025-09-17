from core.auth import create_user

print("FrameTruth AI Forensic Tool v1.0.0 initialized successfully")

username = input("👤 Enter username: ").strip()
password = input("🔑 Enter password: ").strip()
role = input("🎭 Enter role [default=user]: ").strip() or "user"

user_id = create_user(username, password, role)

if user_id is None:
    print("❌ User creation failed.")
else:
    print(f"✅ User created successfully! ID: {user_id}")
