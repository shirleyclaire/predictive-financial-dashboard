from datetime import datetime, timedelta
import random

EXPENSE_CATEGORIES = [
    "Groceries", "Rent", "Utilities", "Transportation", 
    "Entertainment", "Healthcare", "Shopping", "Dining"
]

INCOME_CATEGORIES = [
    "Salary", "Freelance", "Investments", "Bonus"
]

def generate_sample_transactions(user_id: int, months: int = 6):
    transactions = []
    current_date = datetime.now()
    
    for month in range(months):
        # Generate monthly income (1-2 entries)
        for _ in range(random.randint(1, 2)):
            transactions.append({
                "user_id": user_id,
                "amount": round(random.uniform(3000, 6000), 2),
                "category": random.choice(INCOME_CATEGORIES),
                "date": (current_date - timedelta(days=30*month)).date(),
                "type": "income"
            })
        
        # Generate expenses (15-20 entries per month)
        for _ in range(random.randint(15, 20)):
            transactions.append({
                "user_id": user_id,
                "amount": round(random.uniform(10, 500), 2),
                "category": random.choice(EXPENSE_CATEGORIES),
                "date": (current_date - timedelta(days=30*month+random.randint(0, 29))).date(),
                "type": "expense"
            })
    
    return transactions

def generate_sample_goals(user_id: int, count: int = 2):
    goals = []
    for _ in range(count):
        target = random.uniform(5000, 20000)
        goals.append({
            "user_id": user_id,
            "target_amount": round(target, 2),
            "current_amount": round(target * random.uniform(0.1, 0.5), 2),
            "deadline": (datetime.now() + timedelta(days=random.randint(90, 365))).date(),
            "category": random.choice(["Emergency Fund", "Vacation", "Car", "House Down Payment"])
        })
    return goals
