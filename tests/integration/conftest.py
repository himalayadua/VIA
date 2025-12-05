"""
Pytest configuration for integration tests

Provides fixtures and configuration for integration testing.
"""
import pytest
import psycopg2
import requests
import time

# Test database configuration
TEST_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'via_canvas_test',
    'user': 'viacanvas',
    'password': 'viacanvas_dev'
}

# Service URLs
EXPRESS_API_URL = "http://localhost:3000"
PYTHON_API_URL = "http://localhost:8000"


@pytest.fixture(scope="session", autouse=True)
def check_services():
    """Check that required services are running before tests"""
    print("\n🔍 Checking services...")
    
    # Check Express.js backend
    try:
        response = requests.get(f"{EXPRESS_API_URL}/health", timeout=5)
        print("✅ Express.js backend is running")
    except requests.exceptions.RequestException:
        pytest.exit("❌ Express.js backend is not running. Start with: cd server && npm run dev")
    
    # Check Python AI service
    try:
        response = requests.get(f"{PYTHON_API_URL}/health", timeout=5)
        print("✅ Python AI service is running")
    except requests.exceptions.RequestException:
        pytest.exit("❌ Python AI service is not running. Start with: cd chat_service && uvicorn app:app --reload")
    
    # Check PostgreSQL
    try:
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        conn.close()
        print("✅ PostgreSQL database is accessible")
    except psycopg2.OperationalError:
        pytest.exit("❌ PostgreSQL database is not accessible. Check connection settings.")
    
    print("✅ All services are ready\n")


@pytest.fixture(scope="session")
def db_connection():
    """Provide database connection for tests"""
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture
def clean_test_data(db_connection):
    """Clean up test data after each test"""
    yield
    
    # Cleanup logic can be added here if needed
    # For now, each test handles its own cleanup


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add integration marker to all tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
