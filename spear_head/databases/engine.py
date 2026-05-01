from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from databases.db_types.devices.device_db import DeviceDB
from databases.db_types.events.event_db import EventDB
from databases.db_types.campaigns.campaign_db import CampaignDB
from databases.db_types.groups.group_db import GroupDB
from databases.db_types.users.user_db import UserDB
from databases.db_types.rules.rule_db import RuleDB
from databases.db_types.notifications.notification_db import NotificationDB


DATABASE_URL = "sqlite:///databases/presistant/spearit.db"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    connect_args={"check_same_thread": False}
)

SessionMaker = sessionmaker(bind=engine)