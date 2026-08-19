from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TermsVersion:
    identifier: str
    published_on: date


CURRENT_TERMS = TermsVersion(
    identifier="2026-08-19-rzuty-v1",
    published_on=date(2026, 8, 19),
)

CANCELLATION_NOTICE = (
    "Zmiana lub anulowanie Zamówienia Rzutu wymaga kontaktu z nami."
)
TERMS_UPDATED_MESSAGE = (
    "Regulamin został zaktualizowany. Przeczytaj aktualną wersję "
    "i zaakceptuj ją ponownie."
)


class OutdatedTermsVersion(ValueError):
    pass


def require_current_terms(version):
    if version != CURRENT_TERMS.identifier:
        raise OutdatedTermsVersion(TERMS_UPDATED_MESSAGE)
    return CURRENT_TERMS
