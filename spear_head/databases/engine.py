from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///databases/presistant/spearit.db"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    connect_args={"check_same_thread": False}
)

SessionMaker = sessionmaker(bind=engine)