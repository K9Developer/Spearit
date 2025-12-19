from databases.db_types.events.event_db import EventDB
from databases.engine import SessionMaker


def get_event(event_id: int) -> EventDB | None:
    with SessionMaker() as session:
        return session.get(EventDB, event_id)