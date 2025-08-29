"""
Integration tests for the applications API endpoints.

Tests the full request/response cycle for application management,
including database interactions and validation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.core.database import get_db, Base
from backend.models.application import Application


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create test database tables before each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestApplicationsAPI:
    """Test applications API endpoints."""
    
    def test_create_application_success(self, setup_database):
        """Test successful application creation."""
        application_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation"
        }
        
        response = client.post("/api/v1/applications/", json=application_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["full_name"] == "John Doe"
        assert data["date_of_birth"] == "1990-01-15"
        assert data["address_street"] == "123 Main Street"
        assert data["address_city"] == "Anytown"
        assert data["address_state"] == "CA"
        assert data["address_zip"] == "12345"
        assert data["social_security_number"] == "***-**-6789"  # Masked SSN
        assert data["employer_name"] == "Acme Corporation"
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_application_validation_error(self, setup_database):
        """Test application creation with validation errors."""
        application_data = {
            "full_name": "J",  # Too short
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation"
        }
        
        response = client.post("/api/v1/applications/", json=application_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_create_duplicate_application(self, setup_database):
        """Test creating application with duplicate SSN."""
        application_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation"
        }
        
        # Create first application
        response1 = client.post("/api/v1/applications/", json=application_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post("/api/v1/applications/", json=application_data)
        assert response2.status_code == 409
        
        data = response2.json()
        assert "already exists" in data["message"].lower()
    
    def test_get_application_success(self, setup_database):
        """Test successful application retrieval."""
        # First create an application
        application_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation"
        }
        
        create_response = client.post("/api/v1/applications/", json=application_data)
        assert create_response.status_code == 201
        
        application_id = create_response.json()["id"]
        
        # Retrieve the application
        get_response = client.get(f"/api/v1/applications/{application_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        
        assert data["id"] == application_id
        assert data["full_name"] == "John Doe"
        assert data["social_security_number"] == "***-**-6789"  # Masked SSN
    
    def test_get_application_not_found(self, setup_database):
        """Test retrieving non-existent application."""
        fake_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.get(f"/api/v1/applications/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["message"].lower()
    
    def test_update_application_success(self, setup_database):
        """Test successful application update."""
        # First create an application
        application_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation"
        }
        
        create_response = client.post("/api/v1/applications/", json=application_data)
        assert create_response.status_code == 201
        
        application_id = create_response.json()["id"]
        
        # Update the application
        update_data = {
            "employer_name": "Updated Corporation",
            "address_city": "New City"
        }
        
        update_response = client.put(f"/api/v1/applications/{application_id}", json=update_data)
        
        assert update_response.status_code == 200
        data = update_response.json()
        
        assert data["employer_name"] == "Updated Corporation"
        assert data["address_city"] == "New City"
        assert data["full_name"] == "John Doe"  # Unchanged fields remain
    
    def test_update_application_not_found(self, setup_database):
        """Test updating non-existent application."""
        fake_id = "123e4567-e89b-12d3-a456-426614174000"
        update_data = {"employer_name": "Updated Corporation"}
        
        response = client.put(f"/api/v1/applications/{fake_id}", json=update_data)
        
        assert response.status_code == 404
    
    def test_list_applications_success(self, setup_database):
        """Test successful application listing."""
        # Create multiple applications
        for i in range(3):
            application_data = {
                "full_name": f"John Doe {i}",
                "date_of_birth": "1990-01-15",
                "address_street": "123 Main Street",
                "address_city": "Anytown",
                "address_state": "CA",
                "address_zip": "12345",
                "social_security_number": f"123-45-678{i}",
                "employer_name": "Acme Corporation"
            }
            
            response = client.post("/api/v1/applications/", json=application_data)
            assert response.status_code == 201
        
        # List applications
        list_response = client.get("/api/v1/applications/")
        
        assert list_response.status_code == 200
        data = list_response.json()
        
        assert len(data) == 3
        assert all("id" in app for app in data)
        assert all(app["social_security_number"].startswith("***-**-") for app in data)
    
    def test_list_applications_with_status_filter(self, setup_database):
        """Test application listing with status filter."""
        # Create an application
        application_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation"
        }
        
        response = client.post("/api/v1/applications/", json=application_data)
        assert response.status_code == 201
        
        # List pending applications
        list_response = client.get("/api/v1/applications/?status=pending")
        
        assert list_response.status_code == 200
        data = list_response.json()
        
        assert len(data) == 1
        assert data[0]["status"] == "pending"
    
    def test_delete_application_success(self, setup_database):
        """Test successful application deletion."""
        # Create an application
        application_data = {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "address_street": "123 Main Street",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "12345",
            "social_security_number": "123-45-6789",
            "employer_name": "Acme Corporation"
        }
        
        create_response = client.post("/api/v1/applications/", json=application_data)
        assert create_response.status_code == 201
        
        application_id = create_response.json()["id"]
        
        # Delete the application
        delete_response = client.delete(f"/api/v1/applications/{application_id}")
        
        assert delete_response.status_code == 204
        
        # Verify application is deleted
        get_response = client.get(f"/api/v1/applications/{application_id}")
        assert get_response.status_code == 404
    
    def test_delete_application_not_found(self, setup_database):
        """Test deleting non-existent application."""
        fake_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = client.delete(f"/api/v1/applications/{fake_id}")
        
        assert response.status_code == 404