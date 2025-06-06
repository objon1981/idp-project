# Kafka + Zookeeper Setup with Docker

This setup uses [Confluent's Kafka and Zookeeper Docker images](https://hub.docker.com/r/confluentinc/cp-kafka) to run Kafka locally for development and testing purposes.

---

## 📦 Services

- **Zookeeper**: Port `2181`
- **Kafka**:
  - Internal: `PLAINTEXT://kafka:9092`
  - External: `PLAINTEXT_HOST://localhost:29092`

---

## 🚀 How to Use

1. Open a terminal and navigate to this folder:

   ```bash
   cd services/kafka-zookeeper
