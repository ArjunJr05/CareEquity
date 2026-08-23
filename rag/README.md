# SDoH Knowledge Graph Explorer

This project provides an interactive Social Determinants of Health (SDoH) Knowledge Graph built with FastAPI, Neo4j Aura, and Streamlit.

## Components
*   `app.py`: The Streamlit frontend dashboard for exploring the interactive Knowledge Graph.
*   `api.py`: A FastAPI REST backend that serves graph data and metrics.
*   `ingest.py`: A script to process and ingest CSV data into a Neo4j Aura Graph Database.
*   `correlation.py` / `extremes.py`: Scripts for exploring statistical correlations within the dataset.

## Setup Instructions

1. **Install Dependencies:**
   Install all required Python packages using:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables:**
   Ensure you have a `.env` file in the root directory with the following variables configured (for Neo4j connection):
   ```
   NEO4J_URI=neo4j+s://<your-db-id>.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=<your-password>
   FASTAPI_URL=http://127.0.0.1:8000
   ```

## Running the Application

1. **Run the FastAPI Backend:**
   ```bash
   uvicorn api:app --reload
   ```

2. **Run the Streamlit Dashboard (in a separate terminal):**
   ```bash
   streamlit run app.py
   ```

3. **Data Ingestion (Optional):**
   If you need to ingest or refresh data in Neo4j:
   ```bash
   python ingest.py
   ```
