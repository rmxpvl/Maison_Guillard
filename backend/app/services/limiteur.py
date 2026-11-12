import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request

# Rate limiter kept in memory: enough for one API instance (the Render plan of this site). With
# several instances, each would count on its own, so the real limit would be a multiple of it.
_evenements: dict[tuple[str, str], deque] = defaultdict(deque)
_verrou = threading.Lock()
_NETTOYAGE_A = 5000  # entries: drop the ones that have expired, so memory stays bounded


def reinitialiser() -> None:
    with _verrou:
        _evenements.clear()


def adresse_ip(requete: Request) -> str:
    """Address of the visitor. Behind our own proxy (TRUST_PROXY=1) the real address is the LAST
    entry of X-Forwarded-For, added by the proxy; earlier entries come from the visitor and can be
    forged. Without a trusted proxy the header is ignored altogether."""
    if os.environ.get("TRUST_PROXY") == "1":
        transmis = requete.headers.get("x-forwarded-for")
        if transmis:
            return transmis.split(",")[-1].strip()
    return requete.client.host if requete.client else "inconnue"


def verifier(seau: str, identifiant: str, maximum: int, fenetre: int, maintenant: float | None = None) -> None:
    """Counts one request of `identifiant` (an address, an e-mail…) in the bucket `seau`; refuses
    with a 429 when more than `maximum` happened in the last `fenetre` seconds. A refused request
    is not counted: waiting out the window is enough."""
    instant = time.time() if maintenant is None else maintenant
    with _verrou:
        file = _evenements[(seau, identifiant)]
        while file and file[0] <= instant - fenetre:
            file.popleft()
        if len(file) >= maximum:
            attente = int(file[0] + fenetre - instant) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Trop de tentatives : réessayez dans {max(1, (attente + 59) // 60)} minute(s).",
                headers={"Retry-After": str(attente)},
            )
        file.append(instant)
        if len(_evenements) > _NETTOYAGE_A:
            for cle in [c for c, f in _evenements.items() if not f or f[-1] <= instant - 3600]:
                del _evenements[cle]


def limite_ip(seau: str, maximum: int, fenetre: int):
    """Route dependency: at most `maximum` requests per `fenetre` seconds from one address."""

    def dependance(requete: Request) -> None:
        verifier(seau, adresse_ip(requete), maximum, fenetre)

    return Depends(dependance)
