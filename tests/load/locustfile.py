from locust import HttpUser, task, between
from random import choice, uniform
import json

class FinancialDashboardUser(HttpUser):
    wait_time = between(1, 5)
    token = None

    def on_start(self):
        # Login to get token
        response = self.client.post("/api/expenses/token", {
            "username": f"user_{self.user_id}@example.com",
            "password": "testpass123"
        })
        self.token = response.json()["access_token"]

    @task(3)
    def view_monthly_summary(self):
        self.client.get(
            "/api/expenses/transactions/summary/monthly",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(2)
    def add_expense(self):
        expense_data = {
            "amount": round(uniform(10, 1000), 2),
            "category": choice(["groceries", "utilities", "entertainment"]),
            "description": "Load test expense",
            "type": "expense"
        }
        self.client.post(
            "/api/expenses/transactions/",
            json=expense_data,
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def view_predictions(self):
        self.client.get(
            f"/api/predictions/predict/{self.user_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def view_news(self):
        self.client.get("/api/news/")
