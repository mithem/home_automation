"""Constants not necessarily (but might) be bound to single modules
(but are found here to circumvent circular imports (:O))"""
MONTH_TO_DIR = {
    1: "Januar",
    2: "Feburar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}

ABBR_TO_SUBJECT = {
    "D": "Deutsch",
    "E": "Englisch",
    "EK": "Erdkunde",
    "GE": "Geschichte",
    "IF": "Informatik",
    "K": "Kunst",
    "M": "Mathe",
    "PL": "Philosophie",
    "PSE": "Software Engineering",
    "PH": "Physik",
    "SW": "SoWi",
    "SP": "Sport",
}

NETWORK_CALLS_TIMEOUT = 20
