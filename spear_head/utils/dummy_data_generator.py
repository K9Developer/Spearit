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
from databases.db_types.groups.group_db import GroupDB
from databases.db_types.notifications.notification_db import NotificationDB
from databases.db_types.rules.rule_db import RuleDB
from databases.db_types.users.user_db import UserDB
from databases.engine import SessionMaker
from models.devices.device import Device
from models.events.types.campaign import CampaignSeverity, CampaignStatus
from models.managers.device_manager import DeviceManager
from models.managers.group_manager import GroupManager
from models.managers.notification_manager import NotificationManager
from models.managers.user_manager import UserManager
from models.notifications.notification import NotificationType
from models.users.permission import Permission, UserAction
from utils.types import HeartbeatDeviceInformation


@dataclass(slots=True)
class SeedConfig:
    seed: int
    groups: int
    devices: int
    users: int
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

GROUP_TEMPLATES: list[tuple[str, str]] = [
    ("Core Network", "Primary office and central network segment"),
    ("Remote Workforce", "Remote and laptop-heavy endpoints"),
    ("Infrastructure", "Servers, gateways, and critical infra devices"),
    ("Labs", "Testing and staging environments"),
    ("Operations", "Kiosks and ops-focused systems"),
]

USER_TEMPLATES: list[tuple[str, str, str]] = [
    ("Alice Operator", "alice.operator@spearit.local", "Spearit!123"),
    ("Bob Analyst", "bob.analyst@spearit.local", "Spearit!123"),
    ("Charlie Responder", "charlie.responder@spearit.local", "Spearit!123"),
    ("Dana Manager", "dana.manager@spearit.local", "Spearit!123"),
]

NOTIFICATION_TEMPLATES: list[tuple[str, NotificationType]] = [
    ("New suspicious traffic pattern detected during seeded run.", NotificationType.WARNING),
    ("Seeded campaign activity updated for dashboard testing.", NotificationType.INFO),
    ("A high-severity seeded event requires triage.", NotificationType.DANGER),
    ("Device heartbeat drift exceeded expected threshold.", NotificationType.WARNING),
    ("Rule evaluation completed with no blocking actions.", NotificationType.INFO),
    ("Potential lateral movement chain detected.", NotificationType.DANGER),
    ("Campaign timeline refreshed with new findings.", NotificationType.INFO),
    ("Endpoint reported unusual DNS query burst.", NotificationType.WARNING),
]


def to_int(value: object) -> int:
    return int(value)  # type: ignore[arg-type]


def build_mac(index: int) -> str:
    return f"02:AA:BB:CC:{(index // 256) % 256:02X}:{index % 256:02X}"


def build_ip(index: int) -> str:
    third = 20 + ((index // 200) % 20)
    fourth = (index % 200) + 10
    return f"10.20.{third}.{fourth}"


def build_permissions(group_ids: list[int], device_ids: list[int], index: int) -> list[Permission]:
    if not group_ids and not device_ids:
        return []

    if index == 0:
        return [
            Permission(
                type_=UserAction.ROOT,
                affected_groups=group_ids,
                affected_devices=device_ids,
            )
        ]

    group_slice = group_ids[index % max(1, len(group_ids))::2] or group_ids[:1]
    device_slice = device_ids[index % max(1, len(device_ids))::3] or device_ids[:2]
    return [
        Permission(
            type_=UserAction.CREATE_USER,
            affected_groups=group_slice,
            affected_devices=device_slice,
        ),
        Permission(
            type_=UserAction.DELETE_USER,
            affected_groups=group_slice,
            affected_devices=device_slice,
        ),
    ]


def upsert_groups(group_count: int) -> list[int]:
    group_ids: list[int] = []

    for index in range(group_count):
        base_name, description = GROUP_TEMPLATES[index % len(GROUP_TEMPLATES)]
        group_name = f"{base_name} {index + 1:02d}"
        existing = GroupManager.get_group_by_name(group_name)

        if existing is None:
            created = GroupManager.create_group(group_name, description)
            if created.group_id is None:
                continue
            group_ids.append(created.group_id)
        else:
            if existing.group_id is None:
                continue
            GroupManager.update_group_description(existing.group_id, description)
            group_ids.append(existing.group_id)

    return group_ids


def upsert_devices(device_count: int, group_ids: list[int]) -> list[Device]:
    rows: list[Device] = []

    for index in range(device_count):
        profile_name, os_name = DEVICE_PROFILES[index % len(DEVICE_PROFILES)]
        mac = build_mac(index)
        ip = build_ip(index)
        assigned_group_id = group_ids[index % len(group_ids)] if group_ids else None

        heartbeat_info = HeartbeatDeviceInformation(
            device_name=f"{profile_name}-{index + 1:02d}",
            os_details=os_name,
            ip_address=ip,
            mac_address=mac,
        )
        device_id = DeviceManager.submit_device_info(heartbeat_info)
        DeviceManager.set_device_note(device_id, "Seeded for frontend testing")

        existing_groups = list(GroupManager.get_groups_for_device(device_id))
        for group in existing_groups:
            if group.group_id is None:
                continue
            if assigned_group_id is not None and group.group_id == assigned_group_id:
                continue
            GroupManager.remove_device_from_group(group.group_id, device_id)

        if assigned_group_id is not None:
            GroupManager.add_device_to_group(assigned_group_id, device_id)

        device = DeviceManager.get_device_by_id(device_id)
        if device is not None:
            rows.append(device)

    return rows


def upsert_users(user_count: int, group_ids: list[int], device_ids: list[int]) -> list[int]:
    user_ids: list[int] = []

    for index in range(user_count):
        full_name, email, raw_password = USER_TEMPLATES[index % len(USER_TEMPLATES)]
        permissions = build_permissions(group_ids, device_ids, index)
        existing = UserManager.get_user_by_email(email)

        if existing is None:
            created = UserManager.create_user(
                username=full_name,
                email=email,
                raw_password=raw_password,
                permissions=permissions,
            )
            if created is None or created.user_id is None:
                continue
            user_ids.append(created.user_id)
        else:
            existing.full_name = full_name
            existing.permissions = permissions
            existing.token = None
            existing.update_db()
            if existing.user_id is not None:
                user_ids.append(existing.user_id)

    return user_ids


def sync_group_handlers(group_ids: list[int], user_ids: list[int]) -> None:
    if not group_ids or not user_ids:
        return

    for index, group_id in enumerate(group_ids):
        group = GroupManager.get_group_by_id(group_id)
        if group is None:
            continue

        primary_handler = user_ids[index % len(user_ids)]
        secondary_handler = user_ids[(index + 1) % len(user_ids)] if len(user_ids) > 1 else primary_handler
        target_handlers = {primary_handler, secondary_handler}
        current_handlers = set(group.handlers)

        for handler_id in current_handlers - target_handlers:
            GroupManager.remove_handler_from_group(group_id, handler_id)

        for handler_id in target_handlers - current_handlers:
            GroupManager.add_handler_to_group(group_id, handler_id)


def create_notifications(
    user_ids: list[int],
    group_ids: list[int],
    events_created: int,
    rng: random.Random,
) -> int:
    if not user_ids:
        return 0

    created = 0

    notification_target = max(24, len(user_ids) * 10, events_created // 2)
    for index in range(notification_target):
        message, notification_type = NOTIFICATION_TEMPLATES[index % len(NOTIFICATION_TEMPLATES)]
        target_users: list[int]
        if index % 9 == 0:
            target_users = user_ids
        else:
            user_span = 1 if len(user_ids) == 1 else rng.randint(1, min(3, len(user_ids)))
            target_users = rng.sample(user_ids, k=user_span)

        suffix = f" (groups={len(group_ids)}, events={events_created}, batch={index + 1})"
        notification = NotificationManager.create_notification(
            message=message + suffix,
            for_users=target_users,
            type_=notification_type,
            link="/notifications",
        )
        if notification.notification_id is not None:
            created += 1
            if target_users and rng.random() < 0.45:
                read_count = rng.randint(1, len(target_users))
                for user_id in rng.sample(target_users, k=read_count):
                    NotificationManager.mark_notification_as_read(notification.notification_id, user_id)

    return created


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


def create_heartbeats(devices: list[Device], heartbeats_per_device: int, rng: random.Random) -> int:
    total = 0
    now = datetime.now(timezone.utc)

    with SessionMaker() as session:
        for device in devices:
            if device.device_id is None:
                continue
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

            device_db = session.get(DeviceDB, device_id)
            if device_db is not None:
                device_db.last_heartbeat_id = latest_heartbeat_id  # type: ignore

        session.commit()

    return total


def create_events(
    devices: list[Device],
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
            if device.device_id is None:
                continue
            device_id = to_int(device.device_id)

            for index in range(events_per_device):
                rule = rules[(index + device_id) % len(rules)]
                campaign = campaigns[(index + device_id) % len(campaigns)] if campaigns else None

                source_ip = str(device.ip_address or "0.0.0.0")
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
        session.query(NotificationDB).delete()
        session.query(EventDB).delete()
        session.query(HeartbeatDB).delete()
        session.query(CampaignDB).delete()
        session.query(RuleDB).delete()
        session.query(UserDB).delete()
        session.query(DeviceDB).delete()
        session.query(GroupDB).delete()
        session.commit()


def parse_args() -> SeedConfig:
    parser = argparse.ArgumentParser(description="Seed SpearHead DB with dummy test data.")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed for reproducible data")
    parser.add_argument("--groups", type=int, default=3, help="How many groups to upsert")
    parser.add_argument("--devices", type=int, default=12, help="How many devices to upsert")
    parser.add_argument("--users", type=int, default=4, help="How many users to upsert")
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
        groups=max(1, args.groups),
        devices=max(1, args.devices),
        users=max(1, args.users),
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

    group_ids = upsert_groups(config.groups)
    devices = upsert_devices(config.devices, group_ids)
    device_ids = [to_int(device.device_id) for device in devices if device.device_id is not None]
    user_ids = upsert_users(config.users, group_ids, device_ids)
    sync_group_handlers(group_ids, user_ids)

    rules = upsert_rules(group_ids)
    campaigns = upsert_campaigns(config.campaigns, device_ids)
    created_heartbeats = create_heartbeats(devices, config.heartbeats_per_device, rng)
    created_events = create_events(devices, rules, campaigns, config.events_per_device, rng)
    created_notifications = create_notifications(user_ids, group_ids, created_events, rng)

    print("Dummy data generation complete:")
    print(f"- Groups: {len(group_ids)}")
    print(f"- Devices: {len(devices)}")
    print(f"- Users: {len(user_ids)}")
    print(f"- Rules: {len(rules)}")
    print(f"- Campaigns: {len(campaigns)}")
    print(f"- Heartbeats created: {created_heartbeats}")
    print(f"- Events created: {created_events}")
    print(f"- Notifications created: {created_notifications}")
    print(f"- Reset before seeding: {'yes' if config.reset else 'no'}")


def main() -> None:
    seed_database(parse_args())


if __name__ == "__main__":
    main()
