
from models.logger import Logger

Logger.info("Starting SpearHead application...")
from databases import engine
from databases.base import Base
from spear_head import SpearHead
from utils.ai_manager import AIManager

def main():

    # TODO: use alembic when database structure is stable
    Logger.warn("REMEMBER: If changed table, delete DB file to recreate!")
    Logger.info("Initializing database...")
    Base.metadata.create_all(engine.engine)
    AIManager.init()
    sh = SpearHead()
    sh.start()


if __name__ == "__main__":
    main()