"""
Tests for health endpoints.
"""
from fastapi import status
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """
    Test the health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Service is running"
    assert data["data"]["status"] == "ok"


def test_db_health_check(client: TestClient):
    """
    Test the database health check endpoint.
    """
    response = client.get("/health/db")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Database connection is healthy"
    assert data["data"]["status"] == "ok"
