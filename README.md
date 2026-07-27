# CA_Scalable-Cloud-Programming

Link for Dataset: [Kaggle - F1 2020 Race Data](https://www.kaggle.com/datasets/coni57/f1-2020-race-data)

# 🏎️ Formula 1 Real-Time Telemetry & Distributed Stream Ingestion Engine

A high-performance, real-time distributed stream processing and telemetry analytics platform built to ingest, process, and visualize high-frequency Formula 1 race data using dual-layer serving views.

---

## 🏗️ Architecture & Tech Stack

* **Stream Ingestion & Processing:** Apache Kafka (localized broker architecture), Python, PySpark, PySpark SQL, ZooKeeper
* **Storage Tier:** Amazon S3 (Data Lake & JSON Persistence Ledgers)
* **Backend Framework & Dashboard:** Streamlit, Pandas, NumPy
* **Data Visualization:** Plotly (interactive charts & real-time trend feeds)
* **Cloud Environment & CI/CD:** AWS Academy Learner Lab, AWS EC2, automated containerized pipelines

---

## 🚀 Key Features

* **Dual-Layer Serving Views:** Combines batch-historical aggregations with low-latency speed layers for instant insights.
* **Real-Time F1 Telemetry Command:** Live tracking of throttle fusion, speed metrics, RPM distributions, and microsecond stream latencies.
* **Cluster Performance Benchmarking:** Interactive analysis of cluster worker scalability, throughput curves, and execution speedups.
* **Glassmorphism UI:** Custom-styled dark mode dashboard optimized for motorsport telemetry visualization.
