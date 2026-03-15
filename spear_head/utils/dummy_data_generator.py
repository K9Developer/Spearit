from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from databases import engine
from databases.base import Base
from databases.db_types.campaigns.campaign_db import CampaignDB
from databases.db_types.devices.device_db import DeviceDB
from databases.db_types.devices.heartbeat_db import HeartbeatDB
from databases.db_types.events.event_db import EventDB
from databases.db_types.rules.rule_db import RuleDB
from databases.engine import SessionMaker
from models.events.types.campaign import CampaignSeverity, CampaignStatus


@dataclass(slots=True)
class SeedConfig:
    seed: int
    devices: int
    campaigns: int
    heartbeats_per_device: int
    events_per_device: int
    reset: bool


DEVICE_PROFILES: list[tuple[str, str]] = [
    ("Workstation", "Windows 11 Pro"),
    ("Server", "Ubuntu 22.04 LTS"),
    ("Laptop", "macOS 14 Sonoma"),
    ("Kiosk", "Windows 10 IoT"),
    ("Gateway", "Debian 12"),
]

RULE_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Seed Rule - Outbound Suspicious Port",
        "rule_type": "packet",
        "event_types": ["network.send_packet"],
        "conditions": [{"key": "packet.dest.port", "operator": "in", "value": [4444, 8080, 8443]}],
        "responses": ["alert"],
        "priority": 5,
    },
    {
        "name": "Seed Rule - Lateral Movement Pattern",
        "rule_type": "packet",
        "event_types": ["network.send_packet", "network.receive_packet"],
        "conditions": [{"key": "packet.is_connection_establishing", "operator": "equals", "value": True}],
        "responses": ["alert", "isolate"],
        "priority": 8,
    },
    {
        "name": "Seed Rule - Excessive Internal Traffic",
        "rule_type": "packet",
        "event_types": ["network.send_packet"],
        "conditions": [{"key": "packet.dest.ip", "operator": "starts_with", "value": "10.20."}],
        "responses": ["alert"],
        "priority": 3,
    },
]


def to_int(value: object) -> int:
    return int(value)  # type: ignore[arg-type]


def build_mac(index: int) -> str:
    return f"02:AA:BB:CC:{(index // 256) % 256:02X}:{index % 256:02X}"


def build_ip(index: int) -> str:
    third = 20 + ((index // 200) % 20)
    fourth = (index % 200) + 10
    return f"10.20.{third}.{fourth}"


def upsert_devices(device_count: int) -> list[DeviceDB]:
    rows: list[DeviceDB] = []

    with SessionMaker() as session:
        for index in range(device_count):
            profile_name, os_name = DEVICE_PROFILES[index % len(DEVICE_PROFILES)]
            mac = build_mac(index)
            ip = build_ip(index)

            existing = session.query(DeviceDB).filter_by(mac_address=mac).first()
            if existing is None:
                existing = DeviceDB(
                    device_name=f"{profile_name}-{index + 1:02d}",
                    operating_system_details=os_name,
                    last_known_ip_address=ip,
                    mac_address=mac,
                    handlers=[],
                    note="Seeded for frontend testing",
                    groups=[1 + (index % 3)],
                    last_heartbeat_id=None,
                )
                session.add(existing)
            else:
                existing.device_name = f"{profile_name}-{index + 1:02d}"  # type: ignore
                existing.operating_system_details = os_name  # type: ignore
                existing.last_known_ip_address = ip  # type: ignore
                existing.groups = [1 + (index % 3)]  # type: ignore
                existing.note = "Seeded for frontend testing"  # type: ignore

            rows.append(existing)

        session.commit()
        for row in rows:
            session.refresh(row)

    return rows


def upsert_rules(device_group_ids: list[int]) -> list[RuleDB]:
    rows: list[RuleDB] = []

    with SessionMaker() as session:
        for order, template in enumerate(RULE_TEMPLATES, start=1):
            name = str(template["name"])
            priority = int(template["priority"])
            existing = session.query(RuleDB).filter_by(rule_name=name).first()

            if existing is None:
                existing = RuleDB(
                    rule_order=order,
                    rule_type=str(template["rule_type"]),
                    event_types=template["event_types"],
                    conditions=template["conditions"],
                    responses=template["responses"],
                    active_for_groups=device_group_ids,
                    is_active=True,
                    rule_name=name,
                    priority=priority,
                    handlers=[],
                    description="Seeded rule for dashboard filtering and list views",
                )
                session.add(existing)
            else:
                existing.rule_order = order  # type: ignore
                existing.rule_type = str(template["rule_type"])  # type: ignore
                existing.event_types = template["event_types"]  # type: ignore
                existing.conditions = template["conditions"]  # type: ignore
                existing.responses = template["responses"]  # type: ignore
                existing.active_for_groups = device_group_ids  # type: ignore
                existing.is_active = True  # type: ignore
                existing.priority = priority  # type: ignore
                existing.description = "Seeded rule for dashboard filtering and list views"  # type: ignore

            rows.append(existing)

        session.commit()
        for row in rows:
            session.refresh(row)

    return rows


def upsert_campaigns(campaign_count: int, device_ids: list[int]) -> list[CampaignDB]:
    rows: list[CampaignDB] = []
    now = datetime.now(timezone.utc)
    severities = [CampaignSeverity.LOW.value, CampaignSeverity.MEDIUM.value, CampaignSeverity.HIGH.value]
    statuses = [CampaignStatus.ONGOING.value, CampaignStatus.COMPLETED.value, CampaignStatus.ABORTED.value]

    with SessionMaker() as session:
        for index in range(campaign_count):
            name = f"Seed Campaign {index + 1:02d}"
            existing = session.query(CampaignDB).filter_by(name=name).first()
            start_time = now - timedelta(hours=12 + index * 3)
            touched_device_ids = device_ids[index::max(campaign_count, 1)] or device_ids[:3]
            description = f"Seeded campaign #{index + 1} for UI testing"
            detailed = (
                "Automatically generated campaign. "
                "Use this for cards, tables, and detail drawer testing."
            )

            if existing is None:
                existing = CampaignDB(
                    name=name,
                    description=description,
                    detailed_description=detailed,
                    start=start_time,
                    last_updated=start_time + timedelta(hours=1),
                    status=statuses[index % len(statuses)],
                    severity=severities[index % len(severities)],
                    involved_devices=touched_device_ids,
                )
                session.add(existing)
            else:
                existing.description = description  # type: ignore
                existing.detailed_description = detailed  # type: ignore
                existing.start = start_time  # type: ignore
                existing.last_updated = start_time + timedelta(hours=1)  # type: ignore
                existing.status = statuses[index % len(statuses)]  # type: ignore
                existing.severity = severities[index % len(severities)]  # type: ignore
                existing.involved_devices = touched_device_ids  # type: ignore

            rows.append(existing)

        session.commit()
        for row in rows:
            session.refresh(row)

    return rows


def create_heartbeats(devices: list[DeviceDB], heartbeats_per_device: int, rng: random.Random) -> int:
    total = 0
    now = datetime.now(timezone.utc)

    with SessionMaker() as session:
        for device in devices:
            device_id = to_int(device.device_id)
            latest_heartbeat_id: int | None = None

            for offset in range(heartbeats_per_device):
                minutes_ago = (heartbeats_per_device - offset) * 15 + rng.randint(0, 5)
                contacted = {
                    str(rng.randint(1, max(1, len(devices)))): rng.randint(1, 7),
                    str(rng.randint(1, max(1, len(devices)))): rng.randint(1, 7),
                }
                metrics = {
                    "cpu_usage": round(rng.uniform(8.0, 95.0), 2),
                    "memory_usage": round(rng.uniform(15.0, 98.0), 2),
                }

                heartbeat = HeartbeatDB(
                    device_id=device_id,
                    timestamp=now - timedelta(minutes=minutes_ago),
                    contacted_devices=contacted,
                    system_metrics=metrics,
                )
                session.add(heartbeat)
                session.flush()
                latest_heartbeat_id = to_int(heartbeat.heartbeat_id)
                total += 1

            device.last_heartbeat_id = latest_heartbeat_id  # type: ignore

        session.commit()

    return total


def create_events(
    devices: list[DeviceDB],
    rules: list[RuleDB],
    campaigns: list[CampaignDB],
    events_per_device: int,
    rng: random.Random,
) -> int:
    if not rules:
        return 0

    total = 0
    now = datetime.now(timezone.utc)

    with SessionMaker() as session:
        for device in devices:
            device_id = to_int(device.device_id)

            for index in range(events_per_device):
                rule = rules[(index + device_id) % len(rules)]
                campaign = campaigns[(index + device_id) % len(campaigns)] if campaigns else None

                source_ip = str(device.last_known_ip_address or "0.0.0.0")
                dest_ip = f"198.51.100.{(index % 200) + 1}"
                source_port = 1024 + ((index * 17) % 40000)
                dest_port = [443, 53, 80, 22, 8080][index % 5]

                event_data = {
                    "protocol": ["tcp", "udp", "http", "dns"][index % 4],
                    "direction": "OUTBOUND" if index % 2 == 0 else "INBOUND",
                    "source": {
                        "ip": source_ip,
                        "port": source_port,
                        "mac": str(device.mac_address),
                    },
                    "dest": {
                        "ip": dest_ip,
                        "port": dest_port,
                        "mac": f"02:FF:EE:DD:{index % 255:02X}:{device_id % 255:02X}",
                    },
                    "severity_score": rng.randint(15, 99),
                    "is_connection_establishing": bool(index % 2 == 0),
                    "process": {
                        "name": ["chrome.exe", "svchost.exe", "python.exe", "nginx"][index % 4],
                        "pid": 1000 + index,
                    },
                }

                event = EventDB(
                    device_id=device_id,
                    rule_id=to_int(rule.rule_id),
                    campaign_id=to_int(campaign.campaign_id) if campaign is not None else None,
                    event_type="PACKET",
                    event_data=event_data,
                    timestamp=now - timedelta(minutes=rng.randint(5, 240)),
                    response_taken=rng.choice(["ALERT", "ISOLATE", "RUN", None]),
                )
                session.add(event)
                total += 1

        session.commit()

    return total


def clear_seed_target_tables() -> None:
    with SessionMaker() as session:
        session.query(EventDB).delete()
        session.query(HeartbeatDB).delete()
        session.query(CampaignDB).delete()
        session.query(RuleDB).delete()
        session.query(DeviceDB).delete()
        session.commit()


def parse_args() -> SeedConfig:
    parser = argparse.ArgumentParser(description="Seed SpearHead DB with dummy test data.")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed for reproducible data")
    parser.add_argument("--devices", type=int, default=12, help="How many devices to upsert")
    parser.add_argument("--campaigns", type=int, default=4, help="How many campaigns to upsert")
    parser.add_argument("--heartbeats-per-device", type=int, default=8, help="Heartbeats to create per device")
    parser.add_argument("--events-per-device", type=int, default=5, help="Events to create per device")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing records in seeded tables before creating dummy data",
    )

    args = parser.parse_args()
    return SeedConfig(
        seed=args.seed,
        devices=max(1, args.devices),
        campaigns=max(1, args.campaigns),
        heartbeats_per_device=max(1, args.heartbeats_per_device),
        events_per_device=max(0, args.events_per_device),
        reset=bool(args.reset),
    )


def seed_database(config: SeedConfig) -> None:
    rng = random.Random(config.seed)
    Base.metadata.create_all(engine.engine)

    if config.reset:
        clear_seed_target_tables()

    devices = upsert_devices(config.devices)
    device_ids = [to_int(device.device_id) for device in devices]
    group_ids = sorted({1 + (index % 3) for index in range(config.devices)})

    rules = upsert_rules(group_ids)
    campaigns = upsert_campaigns(config.campaigns, device_ids)
    created_heartbeats = create_heartbeats(devices, config.heartbeats_per_device, rng)
    created_events = create_events(devices, rules, campaigns, config.events_per_device, rng)

    print("Dummy data generation complete:")
    print(f"- Devices: {len(devices)}")
    print(f"- Rules: {len(rules)}")
    print(f"- Campaigns: {len(campaigns)}")
    print(f"- Heartbeats created: {created_heartbeats}")
    print(f"- Events created: {created_events}")
    print(f"- Reset before seeding: {'yes' if config.reset else 'no'}")


def main() -> None:
    seed_database(parse_args())


if __name__ == "__main__":
    main()
