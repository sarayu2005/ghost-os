from db.database import get_user, get_user_beliefs, add_belief, delete_belief
import sys

def view_beliefs(username: str):
    """View all beliefs for a user"""
    user_id = get_user(username)
    if not user_id:
        print(f"❌ User '{username}' not found")
        return None
    
    beliefs = get_user_beliefs(user_id)
    if not beliefs:
        print(f"📝 No beliefs found for {username}")
        return user_id
    
    print(f"\n📝 Beliefs for {username}:")
    for b in beliefs:
        print(f"   ID {b['id']}: {b['belief_text']}")
        print(f"      Category: {b['category']}, Strength: {b['strength']}")
    
    return user_id

def add_new_belief(username: str):
    """Add a new belief"""
    user_id = get_user(username)
    if not user_id:
        print(f"❌ User '{username}' not found")
        return

    print(f"\n➕ Adding new belief for {username}...")
    belief = input("   Belief: ").strip()
    category = input("   Category (default: general): ").strip() or "general"
    strength = input("   Strength 0.0-1.0 (default: 0.8): ").strip()
    counter = input("   Counter-argument (steelman the other side, optional): ").strip() or None

    try:
        strength = float(strength) if strength else 0.8
    except:
        strength = 0.8

    strength = max(0.0, min(1.0, strength))
    belief_id = add_belief(user_id, belief, category, strength)

    if counter and belief_id:
        from db.database import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE beliefs SET counter_argument = %s WHERE id = %s", (counter, belief_id))
        conn.commit()
        cur.close()
        conn.close()

    print(f"✅ Belief added!")

def delete_belief_menu(username: str):
    """Delete a belief"""
    user_id = view_beliefs(username)
    if not user_id:
        return
    
    belief_id = input("\nEnter belief ID to delete: ").strip()
    try:
        belief_id = int(belief_id)
        delete_belief(belief_id)
    except:
        print("❌ Invalid ID")

def menu():
    """Interactive menu"""
    print("\n" + "="*60)
    print("🎯 Belief Manager")
    print("="*60)
    
    username = input("Enter username: ").strip()
    
    while True:
        print(f"\n💭 Options for {username}:")
        print("  1. View all beliefs")
        print("  2. Add new belief")
        print("  3. Delete belief")
        print("  4. Exit")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            view_beliefs(username)
        elif choice == "2":
            add_new_belief(username)
        elif choice == "3":
            delete_belief_menu(username)
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    menu()
