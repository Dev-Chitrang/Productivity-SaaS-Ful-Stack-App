from datetime import datetime, timedelta
from typing import List
from dateutil.relativedelta import relativedelta
from app.models.calender import CalendarEvent
from app.modules.calender.enums import RecurrenceFrequency
from app.modules.calender.schema import CalendarOccurrenceResponse


class RecurrenceEngine:
    @staticmethod
    def generate_occurrences_for_event(
        event: CalendarEvent,
        range_start: datetime,
        range_end: datetime,
    ) -> List[CalendarOccurrenceResponse]:
        """
        Expands a recurring event series and returns only the occurrences
        that overlap with [range_start, range_end).

        Occurrences outside the requested window are never generated.
        """
        occurrences: List[CalendarOccurrenceResponse] = []
        event_duration = event.end_time - event.start_time
        interval = event.recurrence_interval or 1

        # Honour the series end date when present
        loop_end = range_end
        if event.recurrence_end_date:
            loop_end = min(range_end, event.recurrence_end_date)

        # Nothing to do if the series hasn't started yet relative to our window
        if event.start_time > loop_end:
            return occurrences

        current_start = event.start_time

        while current_start <= loop_end:
            current_end = current_start + event_duration

            # Include only occurrences that intersect the requested window
            if current_start < range_end and current_end > range_start:
                occurrences.append(
                    CalendarOccurrenceResponse(
                        id=event.id,
                        title=event.title,
                        description=event.description,
                        event_type=event.event_type,
                        color=event.color,
                        start_time=current_start,
                        end_time=current_end,
                        timezone=event.timezone,
                        is_all_day=event.is_all_day,
                        location=event.location,
                        is_recurring=True,
                        recurrence_frequency=event.recurrence_frequency,
                        recurrence_interval=event.recurrence_interval,
                        recurrence_end_date=event.recurrence_end_date,
                    )
                )

            # Advance to next occurrence
            if event.recurrence_frequency == RecurrenceFrequency.DAILY:
                current_start += timedelta(days=interval)

            elif event.recurrence_frequency == RecurrenceFrequency.WEEKLY:
                current_start += timedelta(weeks=interval)

            elif event.recurrence_frequency == RecurrenceFrequency.MONTHLY:
                next_step = current_start + relativedelta(months=interval)
                # Guard against day-overflow (e.g. Jan 31 → Feb 28)
                if next_step.day != current_start.day:
                    current_start = current_start + relativedelta(months=interval * 2)
                    continue
                current_start = next_step

            else:
                break  # Unknown or missing frequency — stop expansion

        return occurrences
