import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from src.main import app
from src.database import Base, get_db
from src import models

# Skip app lifespan touching the real DB file during tests
os.environ.setdefault("TESTING", "1")

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture
def seed_machines(db):
    machines = [
        models.Machine(id=1, name="Washer 1", type="Wash"),
        models.Machine(id=2, name="Dryer 1", type="Dry"),
    ]
    db.add_all(machines)
    db.commit()


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
