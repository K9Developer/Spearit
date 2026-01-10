
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from databases.db_types.campaigns.campaign_db import CampaignDB
from databases.db_types.devices.device import get_or_create_device_db
from databases.db_types.events.event import get_event
from databases.engine import SessionMaker
from models.events.types.event_type import EventType_
from models.devices.device import Device
from models.events.types.packet_event import PacketDirection, PacketEvent
from models.logger import Logger
from utils.campaign_utils import generate_campaign_details

class CampaignStatus(Enum):
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"

class CampaignSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @staticmethod
    def from_str(s: str) -> 'CampaignSeverity':
        s_upper = s.upper()
        if s_upper == "LOW":
            return CampaignSeverity.LOW
        elif s_upper == "MEDIUM":
            return CampaignSeverity.MEDIUM
        elif s_upper == "HIGH":
            return CampaignSeverity.HIGH
        else:
            return CampaignSeverity.LOW

@dataclass(slots=True, init=False)
class Campaign:
    
    initial_event_time: datetime
    last_updated: datetime
    status: CampaignStatus
    severity: CampaignSeverity
    involved_device_ids: list[int]
    events: list[EventType_]
    name: str
    description: str | None = None
    detailed_description: str | None = None
    campaign_id: int | None = None

    def __init__(self) -> None:
        self.name = "Unnamed Campaign"
        self.description = "No description available."
        self.detailed_description = ""
        self.initial_event_time = datetime.fromtimestamp(0)
        self.last_updated = datetime.fromtimestamp(0)
        self.status = CampaignStatus.ONGOING
        self.severity = CampaignSeverity.LOW
        self.involved_device_ids = []
        self.events = []
        self.campaign_id = None

    def add_event(self, event: EventType_) -> None:
        self.events.append(event)
        event_time = datetime.fromtimestamp(event.timestamp_ns / 1e9)
        self.last_updated = event_time

        device_id = get_or_create_device_db(event.device)[1]
        if device_id not in self.involved_device_ids:
            self.involved_device_ids.append(device_id)
        
        if isinstance(event, PacketEvent):
            other_device_mac = event.dest.mac if event.direction == PacketDirection.OUTBOUND else event.source.mac
            other_device_ip = event.dest.ip if event.direction == PacketDirection.OUTBOUND else event.source.ip
            defd = Device.default()
            defd.mac_address = other_device_mac
            defd.ip_address = other_device_ip or "0.0.0.0"
            other_device_id = get_or_create_device_db(defd)[1]
            if other_device_id not in self.involved_device_ids:
                self.involved_device_ids.append(other_device_id)

        if event_time < self.initial_event_time:
            self.initial_event_time = event_time
        
        event.campaign_id = self.campaign_id

    @staticmethod
    def from_db(campaign_db: CampaignDB) -> 'Campaign':
        campaign = Campaign()
        campaign.campaign_id = campaign_db.campaign_id # type: ignore
        campaign.name = campaign_db.name # type: ignore
        campaign.description = campaign_db.description # type: ignore
        campaign.detailed_description = campaign_db.detailed_description # type: ignore
        campaign.initial_event_time = campaign_db.start # type: ignore
        campaign.last_updated = campaign_db.last_updated # type: ignore
        campaign.status = CampaignStatus(campaign_db.status) # type: ignore
        campaign.severity = CampaignSeverity(campaign_db.severity) # type: ignore
        campaign.involved_device_ids = campaign_db.involved_devices or [] # type: ignore
        return campaign

    def to_db(self):
        return CampaignDB(
            name=self.name,
            description=self.description,
            detailed_description=self.detailed_description,
            start=self.initial_event_time,
            last_updated=self.last_updated,
            status=self.status.value,
            severity=self.severity.value,
            involved_devices=self.involved_device_ids
        )

    def update_db(self):
        campaign_id = self.campaign_id
        campaign_db = self.to_db()
        with SessionMaker() as session:
            if campaign_id is None:
                session.add(campaign_db)
                session.commit()
                session.refresh(campaign_db)
                campaign_id = campaign_db.campaign_id
            else:
                campaign_db.campaign_id = campaign_id # type: ignore
                session.merge(campaign_db)
                session.commit()

        self.campaign_id = campaign_id # type: ignore

        for event in self.events:
            if event.campaign_id == campaign_id:
                continue

            if event.campaign_id is not None:
                Logger.warn(f"Event ID {event.event_id} already associated with Campaign ID {event.campaign_id}, cannot reassign to Campaign ID {campaign_id}.")
                continue

            if event.event_id is None:
                event.update_db()
            
            if event.event_id is None:
                Logger.error("Event ID is still None after update_db call.")
                continue
            
            event_db = get_event(event.event_id)
            if event_db is None:
                Logger.error("Failed to retrieve event from DB after update_db call.")
                continue

            with SessionMaker() as session:
                event_db.campaign_id = campaign_id # type: ignore
                event.campaign_id = int(campaign_id) # type: ignore
                session.add(event_db)
                session.commit()
    
    def close_campaign(self):
        self.status = CampaignStatus.COMPLETED
        self.name, self.description, self.detailed_description, sev = generate_campaign_details(self)
        self.severity = CampaignSeverity.from_str(sev)
        self.update_db()

    def __str__(self) -> str:
        return (
            f"Campaign("
            f"name={self.name}, "
            f"status={self.status.value}, "
            f"severity={self.severity.value}, "
            f"initial_event_time={self.initial_event_time}, "
            f"last_updated={self.last_updated}, "
            f"involved_devices_count={len(self.involved_device_ids)}, "
            f"events_count={len(self.events)}"
            f")"
        )
    
    def __repr__(self) -> str:
        return f"""Campaign(
        involved_device_ids={self.involved_device_ids},
        events={[
            repr(event) for event in self.events
        ]}
        )"""
    