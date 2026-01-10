
from models.logger import Logger
from models.rules.rule import Rule

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
    
    # TODO: Remove this
    rul = Rule(name="Test Rule", author_id=1)
    rul.active_for_groups = []
    rul.conditions = [{"key": {"is_key": True,"value": "packet.dst_port"},"operator": "equals","value": {"is_key": False,"value": "6AM="}},{"key": {"is_key": True,"value": "packet.is_connection_establishing"},"operator": "equals","value": {"is_key": False,"value": "AA=="}}]
    rul.responses = ["alert"]
    rul.event_types = ["network.send_packet","network.receive_packet"]
    rul.update_db()
    
    AIManager.init()
    sh = SpearHead()
    sh.start()


if __name__ == "__main__":
    main()