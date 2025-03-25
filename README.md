# Predictive Financial Dashboard

A microservices-based financial health dashboard that combines expense tracking, news aggregation, and predictive analytics.

![Architecture Diagram](./docs/images/architecture.png)

## Features

- 🔐 JWT-based authentication
- 📊 Real-time expense tracking and visualization
- 📈 AI-powered expense predictions
- 📰 Financial news aggregation with sentiment analysis
- 🚀 Microservices architecture
- ⚡ Redis caching
- 🔄 Message queue integration

## Architecture

The system consists of three main microservices:

### Expense Tracker (Port 8001)
- Manages user expenses and transactions
- SQLite database with SQLAlchemy ORM
- Redis caching for performance
- JWT authentication

### News Aggregator (Port 8002)
- Fetches financial news using NewsAPI
- Performs sentiment analysis using FinBERT
- Publishes significant news to RabbitMQ

### Prediction Engine (Port 8003)
- Generates expense forecasts using Prophet
- Integrates news sentiment into predictions
- Provides confidence intervals
- Caches predictions in Redis

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 14+
- Python 3.9+

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/predictive-financial-dashboard.git
cd predictive-financial-dashboard
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configurations
```

3. Start services:
```bash
docker-compose up --build
```

4. Start frontend development server:
```bash
cd frontend
npm install
npm start
```

5. Access the services:
- Dashboard: http://localhost:3000
- API Gateway: http://localhost:80
- API Documentation: http://localhost:80/docs

## API Documentation

See [API Reference](./docs/api-reference.md) for detailed endpoint documentation.

### Authentication

```bash
# Get JWT token
curl -X POST http://localhost/api/expenses/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"

# Use token in requests
curl -X GET http://localhost/api/expenses/transactions/summary/monthly \
  -H "Authorization: Bearer <your_token>"
```

## Production Deployment

### Kubernetes Deployment

1. Configure Kubernetes cluster:
```bash
kubectl create namespace financial-dashboard
kubectl config set-context --current --namespace=financial-dashboard
```

2. Apply configurations:
```bash
kubectl apply -f k8s/
```

See [Deployment Guide](./docs/deployment.md) for detailed instructions.

## Security Considerations

- All endpoints except /api/news are protected with JWT
- Rate limiting: 100 requests/minute per IP
- Sensitive data encryption at rest
- Regular security updates
- Input validation and sanitization
- CORS policy configuration

See [Security Guide](./docs/security.md) for best practices.

## Testing

Run integration tests:
```bash
cd tests
pip install -r requirements.txt
pytest integration/
```

Run load tests:
```bash
locust -f tests/load/locustfile.py --host=http://localhost:80
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push branch: `git push origin feature/your-feature`
5. Submit a pull request

## License

MIT License - see [LICENSE](./LICENSE) for details

## Support

- Create an issue for bug reports
- Join our [Discord community](https://discord.gg/your-server)
- Email: support@example.com
