"""Conservative Spanish date and time interpretation for read-only availability."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta
import re
import unicodedata


@dataclass(frozen=True, slots=True)
class AvailabilityQuery:
    date_from: date
    date_to: date
    modality: str
    time_from: time | None = None
    time_to: time | None = None


_WEEKDAYS = {
    "lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3,
    "viernes": 4, "sabado": 5, "domingo": 6,
}
_AVAILABILITY_WORDS = re.compile(r"\b(disponibilidad|horarios?|turnos?)\b")
_BOOKING_ACTIONS = re.compile(r"\b(separa(?:me|r)?|reserva(?:me|r)?|agenda(?:me|r)?|confirm(?:a|ar))\b")


def is_availability_request(text: str) -> bool:
    normalized = _normalize(text)
    dated_citation = bool(
        re.search(r"\b(?:hay|tienes?)\b[^?]{0,30}\bcitas?\b", normalized)
        and re.search(r"\b(?:hoy|manana|lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b", normalized)
    )
    return (bool(_AVAILABILITY_WORDS.search(normalized)) or dated_citation) and not is_booking_action(text)


def is_booking_action(text: str) -> bool:
    return bool(_BOOKING_ACTIONS.search(_normalize(text)))


def parse_availability_query(text: str, *, today: date) -> AvailabilityQuery | None:
    normalized = _normalize(text)
    target: date | None = None
    if re.search(r"\bhoy\b", normalized):
        target = today
    elif re.search(r"\bmanana\b", normalized):
        target = today + timedelta(days=1)
    else:
        matches = [name for name in _WEEKDAYS if re.search(rf"\b{name}\b", normalized)]
        if len(matches) == 1:
            delta = (_WEEKDAYS[matches[0]] - today.weekday()) % 7
            target = today + timedelta(days=delta)
    if target is None:
        return None

    time_from = time(12) if "en la tarde" in normalized else None
    time_to = time(12) if "en la manana" in normalized or "antes del mediodia" in normalized else None
    after = re.search(r"despues de (?:la(?:s)? )?(\d{1,2})(?::(\d{2}))?", normalized)
    if after:
        hour, minute = int(after.group(1)), int(after.group(2) or 0)
        if hour <= 12:
            hour += 12
        if hour > 23 or minute > 59:
            return None
        time_from = time(hour, minute)
    modality = "virtual" if re.search(r"\b(virtual|videollamada|en linea)\b", normalized) else "in_person"
    return AvailabilityQuery(target, target, modality, time_from, time_to)


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).split())
