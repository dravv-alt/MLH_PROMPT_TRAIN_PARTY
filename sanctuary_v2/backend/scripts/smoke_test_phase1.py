"""
Phase 1 Smoke Test — register → login → /session/start → /turn (text) → /session/end
Creates tables automatically via create_all so the test is self-contained.
"""
import asyncio
import uuid

import httpx

from sanctuary_v2.backend.core.database import engine, Base
from sanctuary_v2.backend.main import app

# Import all models so Base.metadata is populated
from sanctuary_v2.backend.models.user import User          # noqa: F401
from sanctuary_v2.backend.models.session import Session    # noqa: F401
from sanctuary_v2.backend.models.turn import Turn          # noqa: F401
from sanctuary_v2.backend.models.pwm import (              # noqa: F401
    Entity, Thread, UnsaidNode, PrivateLanguageEntry,
)


async def _create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    # Ensure tables exist regardless of alembic state
    await _create_tables()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        suffix = uuid.uuid4().hex[:8]
        username = f"user_{suffix}"
        email = f"user_{suffix}@example.com"
        password = "pass1234"

        # --- 1. Health check ---
        health_resp = await client.get("/health")
        print("health", health_resp.status_code, health_resp.json())
        assert health_resp.status_code == 200, "Health endpoint failed"

        # --- 2. Register ---
        register_payload = {"username": username, "email": email, "password": password}
        register_resp = await client.post("/auth/register", json=register_payload)
        print("register", register_resp.status_code, register_resp.json())
        assert register_resp.status_code == 200, f"Register failed: {register_resp.text}"

        # --- 3. Login ---
        login_payload = {"username_or_email": email, "password": password}
        login_resp = await client.post("/auth/login", json=login_payload)
        print("login", login_resp.status_code, login_resp.json())
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"

        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # --- 4. Start session ---
        start_resp = await client.post("/session/start", headers=headers)
        print("session_start", start_resp.status_code, start_resp.json())
        assert start_resp.status_code == 200, f"Session start failed: {start_resp.text}"
        session_id = start_resp.json().get("session_id")

        # --- 5. Send turn (text only — no external API keys needed for LLM fallback) ---
        turn_payload = {
            "session_id": session_id,
            "text": "I talked to David at the office today and felt tense afterward.",
        }
        turn_resp = await client.post("/turn", headers=headers, json=turn_payload)
        print("turn", turn_resp.status_code, turn_resp.json())
        assert turn_resp.status_code == 200, f"Turn failed: {turn_resp.text}"

        turn_data = turn_resp.json()
        # Verify key response fields
        assert "turn_id" in turn_data, "Missing turn_id"
        assert "response_text" in turn_data, "Missing response_text"
        assert turn_data.get("can_save_to_journal") is True, "Journal flag should be True"

        # --- 6. End session ---
        end_payload = {"session_id": session_id}
        end_resp = await client.post("/session/end", headers=headers, json=end_payload)
        print("session_end", end_resp.status_code, end_resp.json())
        assert end_resp.status_code == 200, f"Session end failed: {end_resp.text}"

    print("\n[PASS] Phase 1 Smoke Test PASSED - all endpoints functional")


if __name__ == "__main__":
    asyncio.run(main())
