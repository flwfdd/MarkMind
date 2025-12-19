#!/bin/bash

# Start SurrealDB
echo "Starting SurrealDB..."
surreal start --log trace --user root --pass root memory &

# Wait for SurrealDB to start
sleep 3

# Initialize database with mock data
echo "Initializing database with mock data..."
python -m app.init_db

echo "Database initialization complete!"
echo "You can now start the FastAPI server with: fastapi dev main.py"
