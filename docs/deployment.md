# Deployment Guide

## Production Setup

### Infrastructure Requirements

- Kubernetes cluster (GKE, EKS, or AKS)
- Redis instance
- RabbitMQ cluster
- Load balancer
- SSL certificates

### Environment Variables

```bash
# Common
REDIS_HOST=redis.production.svc
RABBITMQ_HOST=rabbitmq.production.svc

# News Aggregator
NEWS_API_KEY=your_api_key

# Security
JWT_SECRET=your_secure_secret
```

### Kubernetes Deployment

1. Create namespace:
```bash
kubectl create namespace financial-dashboard
```

2. Create secrets:
```bash
kubectl create secret generic app-secrets \
  --from-literal=JWT_SECRET=your_secret \
  --from-literal=NEWS_API_KEY=your_key
```

3. Deploy services:
```bash
kubectl apply -f k8s/
```

4. Monitor deployment:
```bash
kubectl get pods
kubectl get services
kubectl get ingress
```

### SSL Configuration

1. Install cert-manager:
```bash
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.5.3/cert-manager.yaml
```

2. Configure Let's Encrypt:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your@email.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Monitoring Setup

1. Install Prometheus:
```bash
helm install prometheus prometheus-community/prometheus
```

2. Install Grafana:
```bash
helm install grafana grafana/grafana
```

### Backup Strategy

1. Database backups:
```bash
kubectl create cronjob db-backup --schedule="0 2 * * *" ...
```

2. Configuration backups:
```bash
kubectl get all -o yaml > backup.yaml
```

## Scaling Guidelines

- Scale replicas based on CPU/Memory:
```yaml
apiVersion: autoscaling/v2beta1
kind: HorizontalPodAutoscaler
metadata:
  name: expense-tracker
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: expense-tracker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      targetAverageUtilization: 80
```

## Troubleshooting

### Common Issues

1. Pod crashes:
```bash
kubectl logs <pod-name>
kubectl describe pod <pod-name>
```

2. Service connectivity:
```bash
kubectl exec -it <pod-name> -- curl <service-name>
```

3. Performance issues:
```bash
kubectl top pods
kubectl top nodes
```
