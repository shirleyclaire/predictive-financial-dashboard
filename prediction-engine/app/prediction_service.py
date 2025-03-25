import pandas as pd
import numpy as np
from prophet import Prophet
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List
import json
from .redis_cache import RedisCache

class PredictionService:
    def __init__(self):
        self.model = None
        self.redis_cache = RedisCache()
        self.sentiment_impact = 0

    def prepare_data(self, transactions: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(transactions)
        df = df.rename(columns={'date': 'ds', 'amount': 'y'})
        return df

    async def train_model(self, transactions: List[Dict]):
        df = self.prepare_data(transactions)
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            changepoint_prior_scale=0.05
        )
        self.model.add_regressor('sentiment_impact')
        df['sentiment_impact'] = self.sentiment_impact
        self.model.fit(df)

    async def predict(self, days: int, user_id: str) -> Dict:
        cache_key = f"forecast:{user_id}:{days}"
        cached_result = self.redis_cache.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

        future = self.model.make_future_dataframe(periods=days)
        future['sentiment_impact'] = self.sentiment_impact
        forecast = self.model.predict(future)
        
        result = {
            'dates': forecast['ds'].tail(days).dt.strftime('%Y-%m-%d').tolist(),
            'predictions': forecast['yhat'].tail(days).round(2).tolist(),
            'lower_bound': forecast['yhat_lower'].tail(days).round(2).tolist(),
            'upper_bound': forecast['yhat_upper'].tail(days).round(2).tolist()
        }
        
        self.redis_cache.set(cache_key, json.dumps(result), 3600)
        return result

    def generate_plot(self, forecast_data: Dict) -> Dict:
        fig = go.Figure()

        # Add predictions
        fig.add_trace(go.Scatter(
            x=forecast_data['dates'],
            y=forecast_data['predictions'],
            name='Forecast',
            line=dict(color='blue')
        ))

        # Add confidence interval
        fig.add_trace(go.Scatter(
            x=forecast_data['dates'] + forecast_data['dates'][::-1],
            y=forecast_data['upper_bound'] + forecast_data['lower_bound'][::-1],
            fill='toself',
            fillcolor='rgba(0,100,255,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Confidence Interval'
        ))

        return fig.to_json()

    def update_sentiment_impact(self, sentiment_score: float):
        # Scale sentiment impact between -0.1 and 0.1
        self.sentiment_impact = sentiment_score * 0.1
