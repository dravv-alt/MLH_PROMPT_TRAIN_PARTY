from dataclasses import dataclass

from sqlalchemy import select

from app.models.db import SessionLocal
from app.models.orm import ChatTurn, JournalEntry, utc_now
from app.models.schemas import NarrativeStructure


@dataclass
class JournalSuggestion:
    turn_id: int
    score: float
    reasons: list[str]


class JournalService:
    def __init__(self, session_factory=SessionLocal) -> None:
        self._session_factory = session_factory

    def suggest(self, user_id: str, session_id: str, max_suggestions: int) -> tuple[list[int], list[str]]:
        turns = self._get_turn_rows(user_id=user_id, session_id=session_id)
        if not turns:
            return [], []

        suggestions: list[JournalSuggestion] = []
        previous_structure: NarrativeStructure | None = None

        for turn in turns:
            structure = NarrativeStructure.model_validate(turn.narrative_structure)
            reasons: list[str] = []
            score = 0.0

            if structure.temporal.resolution_state in {"emerging_clarity", "partial_resolution", "integrated", "reopened"}:
                reasons.append("resolution_change")
                score += 1.0

            if structure.temporal.is_recurring:
                reasons.append("pattern_recognition")
                score += 0.8

            if structure.temporal.resolution_state == 'emerging_clarity':
                reasons.append("insight_marker")
                score += 0.6

            if previous_structure is not None:
                intensity_delta = abs(structure.reaction.intensity - previous_structure.reaction.intensity) if structure.reaction.intensity is not None and previous_structure.reaction.intensity is not None else 0
                known_change = 'unknown' not in (structure.reaction.primary_reaction, previous_structure.reaction.primary_reaction) and structure.reaction.primary_reaction != previous_structure.reaction.primary_reaction
                if intensity_delta >= 0.15 or known_change:
                    reasons.append("emotional_shift")
                    score += 0.7

            previous_structure = structure

            if reasons:
                suggestions.append(
                    JournalSuggestion(
                        turn_id=turn.turn_index,
                        score=score,
                        reasons=list(dict.fromkeys(reasons)),
                    )
                )

        suggestions.sort(key=lambda item: (item.score, item.turn_id), reverse=True)
        selected = suggestions[:max_suggestions]

        suggested_turn_ids = sorted([item.turn_id for item in selected])
        reasoning_labels: list[str] = []
        for item in selected:
            for reason in item.reasons:
                if reason not in reasoning_labels:
                    reasoning_labels.append(reason)

        return suggested_turn_ids, reasoning_labels

    def create_entry(
        self,
        user_id: str,
        session_id: str,
        selected_turn_ids: list[int],
        entry_title: str | None,
        user_reflection_text: str | None,
    ) -> JournalEntry:
        turns = self._get_turn_rows(user_id=user_id, session_id=session_id)
        if not turns:
            raise ValueError("Session not found.")

        available_turn_ids = {turn.turn_index for turn in turns}
        invalid_ids = [turn_id for turn_id in selected_turn_ids if turn_id not in available_turn_ids]
        if invalid_ids:
            raise ValueError("Selected turn ids are not valid for this session.")

        deduped_turn_ids = sorted(set(selected_turn_ids))
        summary_snapshot, reasoning_labels = self._build_summary(turns=turns, selected_turn_ids=deduped_turn_ids)

        with self._session_factory() as db:
            entry = JournalEntry(
                user_id=user_id,
                session_id=session_id,
                selected_turn_ids=deduped_turn_ids,
                reasoning_labels=reasoning_labels,
                entry_title=self._normalize_text(entry_title),
                user_reflection_text=self._normalize_text(user_reflection_text),
                summary_snapshot=summary_snapshot,
                updated_at=utc_now(),
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry

    def list_entries(self, user_id: str) -> list[JournalEntry]:
        with self._session_factory() as db:
            return db.scalars(
                select(JournalEntry)
                .where(JournalEntry.user_id == user_id)
                .order_by(JournalEntry.updated_at.desc(), JournalEntry.id.desc())
            ).all()

    def get_entry(self, user_id: str, entry_id: int) -> JournalEntry | None:
        with self._session_factory() as db:
            return db.scalar(
                select(JournalEntry).where(
                    JournalEntry.user_id == user_id,
                    JournalEntry.id == entry_id,
                )
            )

    def update_entry(
        self,
        user_id: str,
        entry_id: int,
        entry_title: str | None,
        user_reflection_text: str | None,
        update_title: bool,
        update_reflection: bool,
    ) -> JournalEntry | None:
        with self._session_factory() as db:
            entry = db.scalar(
                select(JournalEntry).where(
                    JournalEntry.user_id == user_id,
                    JournalEntry.id == entry_id,
                )
            )
            if entry is None:
                return None

            if update_title:
                entry.entry_title = self._normalize_text(entry_title)
            if update_reflection:
                entry.user_reflection_text = self._normalize_text(user_reflection_text)
            entry.updated_at = utc_now()
            db.commit()
            db.refresh(entry)
            return entry

    def delete_entry(self, user_id: str, entry_id: int) -> bool:
        with self._session_factory() as db:
            entry = db.scalar(
                select(JournalEntry).where(
                    JournalEntry.user_id == user_id,
                    JournalEntry.id == entry_id,
                )
            )
            if entry is None:
                return False

            db.delete(entry)
            db.commit()
            return True

    def session_exists(self, user_id: str, session_id: str) -> bool:
        with self._session_factory() as db:
            return (
                db.scalar(
                    select(ChatTurn.id).where(
                        ChatTurn.user_id == user_id,
                        ChatTurn.session_id == session_id,
                    )
                )
                is not None
            )

    def _get_turn_rows(self, user_id: str, session_id: str) -> list[ChatTurn]:
        with self._session_factory() as db:
            return db.scalars(
                select(ChatTurn)
                .where(
                    ChatTurn.user_id == user_id,
                    ChatTurn.session_id == session_id,
                )
                .order_by(ChatTurn.turn_index.asc())
            ).all()

    def _build_summary(self, turns: list[ChatTurn], selected_turn_ids: list[int]) -> tuple[str, list[str]]:
        selected_set = set(selected_turn_ids)
        selected_turns = [turn for turn in turns if turn.turn_index in selected_set]
        structures = [NarrativeStructure.model_validate(turn.narrative_structure) for turn in selected_turns]
        if not structures:
            return "No structural highlights available.", []

        first = structures[0]
        last = structures[-1]

        reasoning_labels: list[str] = []
        if any(item.temporal.is_recurring for item in structures):
            reasoning_labels.append("pattern_recognition")
        if first.temporal.resolution_state != last.temporal.resolution_state:
            reasoning_labels.append("resolution_change")
        if any(item.temporal.resolution_state == 'emerging_clarity' for item in structures):
            reasoning_labels.append("insight_marker")

        if len(structures) >= 2:
            intensity_delta = abs(structures[-1].reaction.intensity - structures[0].reaction.intensity) if structures[-1].reaction.intensity is not None and structures[0].reaction.intensity is not None else 0
            if intensity_delta >= 0.15:
                reasoning_labels.append("emotional_shift")

        summary_snapshot = (
            f"Pattern from {first.event.event_type} to {last.event.event_type}; "
            f"resolution moved {first.temporal.resolution_state} -> {last.temporal.resolution_state}; "
            f"latest signature: {last.temporal.pattern_signature}."
        )

        return summary_snapshot, reasoning_labels

    def _normalize_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized if normalized else None
