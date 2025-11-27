from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlmodel import Session, select

from app.db.models_wbs import (
    Wbs6,
    Wbs7,
    WbsSpaziale,
    WbsVisibility,
    WbsVisibilityKind,
)


@dataclass(frozen=True)
class WbsVisibilityEntry:
    level: int
    node_id: int
    code: str
    description: str | None
    hidden: bool


@dataclass(frozen=True)
class _NodeDescriptor:
    level: int
    kind: WbsVisibilityKind
    node_id: int
    code: str
    description: str | None


class WbsVisibilityService:
    """Gestisce le preferenze di visibilità dei raggruppatori WBS (1-7)."""

    LEVEL_LABELS = {
        1: "WBS 1 - Lotto/Edificio",
        2: "WBS 2 - Livelli",
        3: "WBS 3 - Ambiti Omogenei",
        4: "WBS 4 - Appalto/Fase",
        5: "WBS 5 - Elementi Funzionali",
        6: "WBS 6 - Categorie Merceologiche",
        7: "WBS 7 - Raggruppatori EPU",
    }

    @staticmethod
    def list_visibility(session: Session, commessa_id: int) -> list[WbsVisibilityEntry]:
        descriptors = WbsVisibilityService._collect_descriptors(session, commessa_id)
        vis_rows = session.exec(
            select(WbsVisibility).where(WbsVisibility.commessa_id == commessa_id)
        ).all()
        vis_map = {(row.kind, row.node_id): row for row in vis_rows}

        entries: list[WbsVisibilityEntry] = []
        for descriptor in descriptors:
            hidden_row = vis_map.get((descriptor.kind, descriptor.node_id))
            entries.append(
                WbsVisibilityEntry(
                    level=descriptor.level,
                    node_id=descriptor.node_id,
                    code=descriptor.code,
                    description=descriptor.description,
                    hidden=bool(hidden_row.hidden) if hidden_row else False,
                )
            )

        entries.sort(key=lambda item: (item.level, item.code, item.description or ""))
        return entries

    @staticmethod
    def update_visibility(
        session: Session,
        commessa_id: int,
        updates: Iterable[tuple[int, int, bool]],
    ) -> list[WbsVisibilityEntry]:
        updates_list = list(updates)
        if not updates_list:
            return WbsVisibilityService.list_visibility(session, commessa_id)

        descriptors = WbsVisibilityService._collect_descriptors(session, commessa_id)
        descriptor_map = {
            (desc.level, desc.node_id): desc for desc in descriptors
        }

        for level, node_id, hidden in updates_list:
            descriptor = descriptor_map.get((level, node_id))
            if not descriptor:
                raise ValueError(
                    f"Nodo WBS livello {level} id {node_id} non appartiene alla commessa"
                )

            visibility = session.exec(
                select(WbsVisibility).where(
                    WbsVisibility.commessa_id == commessa_id,
                    WbsVisibility.kind == descriptor.kind,
                    WbsVisibility.node_id == node_id,
                )
            ).first()

            if hidden:
                if not visibility:
                    visibility = WbsVisibility(
                        commessa_id=commessa_id,
                        kind=descriptor.kind,
                        node_id=node_id,
                        hidden=True,
                    )
                else:
                    visibility.hidden = True
                session.add(visibility)
            elif visibility:
                session.delete(visibility)

        session.commit()
        return WbsVisibilityService.list_visibility(session, commessa_id)

    @staticmethod
    def hidden_codes_by_level(
        session: Session,
        commessa_id: int,
    ) -> dict[int, set[str]]:
        entries = WbsVisibilityService.list_visibility(session, commessa_id)
        hidden: dict[int, set[str]] = {}
        for entry in entries:
            if not entry.hidden:
                continue
            if not entry.code:
                continue
            hidden.setdefault(entry.level, set()).add(entry.code)
        return hidden

    @staticmethod
    def _collect_descriptors(
        session: Session,
        commessa_id: int,
    ) -> list[_NodeDescriptor]:
        descriptors: list[_NodeDescriptor] = []

        spaziali = session.exec(
            select(WbsSpaziale)
            .where(WbsSpaziale.commessa_id == commessa_id)
            .order_by(WbsSpaziale.level, WbsSpaziale.code)
        ).all()
        for node in spaziali:
            descriptors.append(
                _NodeDescriptor(
                    level=node.level,
                    kind=WbsVisibilityKind.spaziale,
                    node_id=node.id,
                    code=node.code,
                    description=node.description,
                )
            )

        wbs6_nodes = session.exec(
            select(Wbs6)
            .where(Wbs6.commessa_id == commessa_id)
            .order_by(Wbs6.code)
        ).all()
        for node in wbs6_nodes:
            descriptors.append(
                _NodeDescriptor(
                    level=6,
                    kind=WbsVisibilityKind.wbs6,
                    node_id=node.id,
                    code=node.code,
                    description=node.description,
                )
            )

        wbs7_nodes = session.exec(
            select(Wbs7)
            .where(Wbs7.commessa_id == commessa_id)
            .order_by(Wbs7.code)
        ).all()
        for node in wbs7_nodes:
            descriptors.append(
                _NodeDescriptor(
                    level=7,
                    kind=WbsVisibilityKind.wbs7,
                    node_id=node.id,
                    code=node.code or "",
                    description=node.description,
                )
            )

        descriptors.sort(key=lambda item: (item.level, item.code, item.description or ""))
        return descriptors
