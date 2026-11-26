import uuid
from datetime import timedelta

from polar.event_type.service import event_type_service
from polar.event_type.sorting import EventTypesSortProperty
from polar.integrations.tinybird.service import TinybirdEventTypeStats
from polar.kit.utils import utc_now
from polar.models import EventType
from polar.models.event import EventSource


def _stats(
    organization_id: uuid.UUID,
    name: str,
    *,
    source: EventSource = EventSource.user,
    occurrences: int = 1,
    hours_ago: int = 0,
) -> TinybirdEventTypeStats:
    now = utc_now()
    return TinybirdEventTypeStats(
        organization_id=organization_id,
        name=name,
        source=source,
        occurrences=occurrences,
        first_seen=now - timedelta(hours=hours_ago + 1),
        last_seen=now - timedelta(hours=hours_ago),
    )


def _event_type(organization_id: uuid.UUID, name: str, label: str) -> EventType:
    return EventType(organization_id=organization_id, name=name, label=label)


class TestSortStats:
    def test_label(self) -> None:
        organization_id = uuid.uuid4()
        stats = [
            _stats(organization_id, "aaa.event"),
            _stats(organization_id, "zzz.event"),
        ]
        event_types_by_key = {
            (organization_id, "aaa.event"): _event_type(
                organization_id, "aaa.event", "Zebra"
            ),
            (organization_id, "zzz.event"): _event_type(
                organization_id, "zzz.event", "apple"
            ),
        }

        ascending = event_type_service._sort_stats(
            stats,
            event_types_by_key,
            [(EventTypesSortProperty.event_type_label, False)],
        )
        descending = event_type_service._sort_stats(
            stats,
            event_types_by_key,
            [(EventTypesSortProperty.event_type_label, True)],
        )

        assert [s.name for s in ascending] == ["zzz.event", "aaa.event"]
        assert [s.name for s in descending] == ["aaa.event", "zzz.event"]

    def test_system_event_label(self) -> None:
        organization_id = uuid.uuid4()
        stats = [
            _stats(organization_id, "user.event"),
            _stats(organization_id, "benefit.granted", source=EventSource.system),
        ]
        event_types_by_key = {
            (organization_id, "user.event"): _event_type(
                organization_id, "user.event", "Custom Event"
            ),
        }

        result = event_type_service._sort_stats(
            stats,
            event_types_by_key,
            [(EventTypesSortProperty.event_type_label, False)],
        )

        assert [s.name for s in result] == ["benefit.granted", "user.event"]

    def test_label_then_secondary_criterion(self) -> None:
        organization_id = uuid.uuid4()
        stats = [
            _stats(organization_id, "a.event", occurrences=1),
            _stats(organization_id, "b.event", occurrences=5),
            _stats(organization_id, "c.event", occurrences=3),
        ]
        event_types_by_key = {
            (organization_id, "a.event"): _event_type(
                organization_id, "a.event", "Same"
            ),
            (organization_id, "b.event"): _event_type(
                organization_id, "b.event", "Same"
            ),
            (organization_id, "c.event"): _event_type(
                organization_id, "c.event", "Another"
            ),
        }

        result = event_type_service._sort_stats(
            stats,
            event_types_by_key,
            [
                (EventTypesSortProperty.event_type_label, False),
                (EventTypesSortProperty.occurrences, True),
            ],
        )

        assert [s.name for s in result] == ["c.event", "b.event", "a.event"]
