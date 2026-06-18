from db.database import create_user, add_belief, get_user_beliefs
import json

BELIEF_CATEGORIES = {
    "1": ("AI Safety", "AI safety, alignment, responsible AI development"),
    "2": ("Open Source", "Open source software, community-driven development"),
    "3": ("Decentralization", "Decentralized systems, blockchain, Web3"),
    "4": ("Privacy", "Privacy rights, data protection, anonymity"),
    "5": ("Education", "Learning, knowledge sharing, educational access"),
    "6": ("Climate", "Climate action, sustainability, environmental impact"),
    "7": ("Accessibility", "Accessibility for disabled users, inclusive design"),
}

def run_onboarding():
    """Interactive onboarding to capture user beliefs"""
    print("\n" + "="*60)
    print("🎯 Welcome to Ghost OS - Onboarding Interview")
    print("="*60)
    
    # Step 1: Get username
    username = input("\n👤 Enter your username: ").strip()
    user_id = create_user(username)
    
    print(f"\n✅ Welcome, {username}!")
    print("\n📚 Let's capture your beliefs about tech & society...")
    
    # Step 2: Select interest categories
    print("\n🎯 Which topics matter to you? (select multiple by entering numbers, comma-separated)")
    for key, (name, desc) in BELIEF_CATEGORIES.items():
        print(f"  {key}. {name}: {desc}")
    
    selected = input("\nEnter numbers (e.g., 1,3,5): ").strip().split(",")
    selected_categories = [BELIEF_CATEGORIES[s.strip()] for s in selected if s.strip() in BELIEF_CATEGORIES]
    
    # Step 3: For each category, get specific beliefs
    beliefs = []
    for category_name, category_desc in selected_categories:
        print(f"\n💭 {category_name}:")
        print(f"   {category_desc}")
        
        belief_text = input(f"   What's your belief about {category_name}? (e.g., 'AI safety is critical'): ").strip()
        
        if belief_text:
            strength = input("   How strongly do you believe this? (0.0-1.0, default 0.8): ").strip()
            try:
                strength = float(strength)
            except:
                strength = 0.8
            
            belief_id = add_belief(user_id, belief_text, category_name, strength)
            beliefs.append({
                "id": belief_id,
                "text": belief_text,
                "category": category_name,
                "strength": strength
            })
    
    # Step 4: Confirmation
    print("\n" + "="*60)
    print(f"✅ Onboarding Complete!")
    print(f"   User: {username} (ID: {user_id})")
    print(f"   Beliefs captured: {len(beliefs)}")
    print("="*60)
    
    for i, belief in enumerate(beliefs, 1):
        print(f"   {i}. {belief['text']} ({belief['strength']})")
    
    print("\n✅ Your profile is ready! Ghost OS will now match news to your beliefs.")
    
    return user_id, beliefs

if __name__ == "__main__":
    user_id, beliefs = run_onboarding()
    
    # Verify beliefs were stored
    stored_beliefs = get_user_beliefs(user_id)
    print(f"\n📝 Verification - Beliefs in database: {len(stored_beliefs)}")
    for belief in stored_beliefs:
        print(f"   - {belief['belief_text']} ({belief['strength']})")
