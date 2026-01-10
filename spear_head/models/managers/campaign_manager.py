from datetime import datetime
from typing import Generator

from databases.db_types.campaigns.campaign_db import CampaignDB
from models.logger import Logger
from databases.engine import SessionMaker
from models.events.types.packet_event import PacketEvent
from models.events.types.event import EventKind
from models.events.types.campaign import Campaign, CampaignSeverity
from models.events.types.event_type import EventType_
from constants.constants import CAMPAIGN_MATCH_SCORE_THRESHOLD, CAMPAIGN_ONGOING_TIMEOUT
from models.managers.event_manager import EventManager
from utils.packet_event_utils import fix_event_process, same_conversation_score

# TODO: Merge campaigns
class CampaignManager:

    ongoing_campaigns: list[Campaign] = []

    @staticmethod
    def _score_packet_event_match(event1: EventType_, event2: EventType_) -> float:
        score = 0.0

        if not isinstance(event1, PacketEvent) or not isinstance(event2, PacketEvent):
            return score

        pkt1: PacketEvent = event1  # type: ignore
        pkt2: PacketEvent = event2  # type: ignore

        return same_conversation_score(pkt1, pkt2)

    @staticmethod
    def _score_events_match(event1: EventType_, event2: EventType_) -> float:
        score = 0.0

        if event1.device.mac_address == event2.device.mac_address:
            score += 0.5

        if event1.violation_type == event2.violation_type:
            score += 0.25

        if event1.violated_rule_id == event2.violated_rule_id:
            score += 0.25

        if event1.event_type == event2.event_type:
            score += 0.15

            if event1.event_type == EventKind.PACKET:
                score += CampaignManager._score_packet_event_match(event1, event2) * 0.50
            # TODO: Add more event type specific scoring here

        return score / (0.5 + 0.25 + 0.25 + 0.15 + 0.50) # Normalize score
        

    @staticmethod
    def _score_campaign_match(event: EventType_, campaign: Campaign) -> float:
        total_score = 0.0
        for campaign_event in campaign.events:
            score = CampaignManager._score_events_match(event, campaign_event)
            total_score += score
        
        if len(campaign.events) == 0:
            return 0.0
        
        return total_score / len(campaign.events)

    @staticmethod
    def _process_event(event: EventType_):
        best_campaign: Campaign | None = None
        best_score = 0.0

        for camp_index, campaign in enumerate(CampaignManager.ongoing_campaigns):

            if abs(datetime.now().timestamp() - campaign.last_updated.timestamp()) > CAMPAIGN_ONGOING_TIMEOUT:
                Logger.debug(f"Closing campaign...")
                campaign.close_campaign()
                CampaignManager.ongoing_campaigns.pop(camp_index)
                Logger.debug(f"Closed campaign ID {campaign.campaign_id} due to inactivity.")
            
            score = CampaignManager._score_campaign_match(event, campaign)
            if score > best_score:
                best_score = score
                best_campaign = campaign

        if best_campaign is not None and best_score * 100 >= CAMPAIGN_MATCH_SCORE_THRESHOLD:
            changed_events = fix_event_process(best_campaign, event)
            for changed_event in changed_events:
                if changed_event.event_id is None: continue
                event_db = event.to_db()
                event_db.event_id = event.event_id # type: ignore
                with SessionMaker() as session:
                    session.merge(event_db)
                    session.commit()

            best_campaign.add_event(event)
            best_campaign.update_db()
            event.update_db()
        else:
            Logger.debug("Creating new campaign for event.")
            new_campaign = Campaign()
            new_campaign.add_event(event)
            new_campaign.update_db()
            CampaignManager.ongoing_campaigns.append(new_campaign)
    
    @staticmethod
    def _process_campaigns():
        pass # TODO: merge campaigns into bigger campaigns

    # --------- Public Methods ---------

    @staticmethod
    def get_ongoing_campaigns() -> list[Campaign]:
        return CampaignManager.ongoing_campaigns
    
    @staticmethod
    def get_all_campaigns() -> Generator[Campaign, None, None]:
        with SessionMaker() as session:
            campaign_dbs = session.query(CampaignDB).all()
            for campaign_db in campaign_dbs:
                campaign = Campaign.from_db(campaign_db)
                yield campaign
             
    @staticmethod
    def get_campaign_by_id(campaign_id: int) -> Campaign | None:
        for campaign in CampaignManager.get_all_campaigns():
            if campaign.campaign_id == campaign_id:
                return campaign
        return None
    
    @staticmethod
    def rename_campaign(campaign_id: int, new_name: str) -> bool:
        campaign = CampaignManager.get_campaign_by_id(campaign_id)
        if campaign is None:
            return False
        campaign.name = new_name
        campaign.update_db()
        return True
    
    @staticmethod
    def change_campaign_severity(campaign_id: int, new_severity: str) -> bool:
        campaign = CampaignManager.get_campaign_by_id(campaign_id)
        if campaign is None:
            return False
        campaign.severity = CampaignSeverity.from_str(new_severity)
        campaign.update_db()
        return True
    
    @staticmethod
    def change_campaign_description(campaign_id: int, new_description: str) -> bool:
        campaign = CampaignManager.get_campaign_by_id(campaign_id)
        if campaign is None:
            return False
        campaign.description = new_description
        campaign.update_db()
        return True
    
    @staticmethod
    def move_event_to_campaign(campaign_id: int, event_id: int) -> bool:
        campaign = CampaignManager.get_campaign_by_id(campaign_id)
        if campaign is None:
            return False
        
        event = EventManager.get_event_by_id(event_id)
        if event is None:
            return False
        
        campaign.add_event(event)
        event.update_db()
        campaign.update_db()
        return True
        