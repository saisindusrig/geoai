"""Pytest fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.main import app
from app.db.session import get_db


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_boundary():
    return {
        "type": "Polygon",
        "coordinates": [[
            [77.5920, 12.9700],
            [77.5975, 12.9700],
            [77.5975, 12.9735],
            [77.5920, 12.9735],
            [77.5920, 12.9700],
        ]],
    }


@pytest.fixture()
def sample_alignment():
    return {
        "type": "LineString",
        "coordinates": [
            [77.5925, 12.9710],
            [77.59475, 12.97175],
            [77.5970, 12.9725],
        ],
    }
