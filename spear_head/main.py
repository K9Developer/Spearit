
from models.logger import Logger
from models.managers.user_manager import UserManager
from models.rules.rule import Rule
from models.users.permission import Permission
# from utils.dummy_data_generator import SeedConfig, seed_database
# from utils.dummy_data_generator import seed_database

Logger.info("Starting SpearHead application...")
from databases import engine
from databases.base import Base
from spear_head import SpearHead
from utils.ai_utils import AIManager

from databases.db_types.users.user_db import UserDB

def main():
    #TODO: ROOT SHOULD SEE AND HANDLE ALL GORUPS/DEVICES
    

    # TODO: use alembic when database structure is stable
    Logger.warn("REMEMBER: If changed table, delete DB file to recreate!")
    Logger.info("Initializing database...")
    Base.metadata.create_all(engine.engine)
    
    # TODO: Remove this
    rul = Rule(name="Test Rule", author_id=1)
    rul.active_for_groups = [1]
    rul.conditions = [{"key": {"is_key": True,"value": "packet.src_port"},"operator": "equals","value": {"is_key": False,"value": "6AM="}},{"key": {"is_key": True,"value": "packet.is_connection_establishing"},"operator": "equals","value": {"is_key": False,"value": "AA=="}}]
    rul.responses = ["alert"]
    rul.event_types = ["network.send_packet","network.receive_packet"]
    rul.update_db()
    
    # TODO: Remove this
    # seed_database(
    #     SeedConfig(
    #         seed=random.randint(0, 1000000),
    #         groups=3,
    #         devices=20,
    #         users=4,
    #         campaigns=3,
    #         heartbeats_per_device=30,
    #         events_per_device=10,
    #         reset=True
    #     )
    # )

    # TODO: Remove this
    # temp super user
    UserManager.create_user(
            username="Admin User",
            email="a@a.com",
            raw_password="12345678",
            permissions=[Permission.root()],
        )

    AIManager.init()
    sh = SpearHead()
    sh.start()


if __name__ == "__main__":
    main()