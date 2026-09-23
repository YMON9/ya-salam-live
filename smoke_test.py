"""End-to-end smoke test for a host and a phone joining the same room."""

from __future__ import annotations

import asyncio
import json

import websockets


URL = "ws://127.0.0.1:8000/ws"


async def receive_until(socket, predicate):
    for _ in range(20):
        message = json.loads(await asyncio.wait_for(socket.recv(), timeout=2))
        if predicate(message):
            return message
    raise AssertionError("Expected WebSocket state was not received")


async def main() -> None:
    async with websockets.connect(URL) as host, websockets.connect(URL) as phone:
        await host.send(json.dumps({"action": "create", "name": "المضيف"}))
        welcome = await receive_until(host, lambda m: m.get("type") == "welcome")
        code = welcome["room"]
        await receive_until(host, lambda m: m.get("type") == "state")

        await phone.send(json.dumps({"action": "join", "room": code, "name": "اللاعب"}))
        await receive_until(phone, lambda m: m.get("type") == "welcome")
        joined = await receive_until(phone, lambda m: m.get("type") == "state")
        assert len(joined["players"]) == 2
        await receive_until(host, lambda m: m.get("type") == "state" and len(m["players"]) == 2)

        await host.send(json.dumps({"action": "start", "rounds": 8}))
        host_game = await receive_until(host, lambda m: m.get("phase") == "game")
        phone_game = await receive_until(phone, lambda m: m.get("phase") == "game")
        assert host_game["room"] == phone_game["room"] == code
        assert host_game["card"]["prompt"] is None

        await host.send(json.dumps({"action": "reveal"}))
        host_reveal = await receive_until(host, lambda m: m.get("revealed") is True)
        phone_reveal = await receive_until(phone, lambda m: m.get("revealed") is True)
        assert host_reveal["card"]["prompt"] == phone_reveal["card"]["prompt"]
        assert host_reveal["deadline"] == phone_reveal["deadline"]

        base_points = host_reveal["card"]["points"]
        await host.send(json.dumps({"action": "power", "power": "double"}))
        doubled = await receive_until(host, lambda m: m.get("card", {}).get("points") == base_points * 2)
        await receive_until(phone, lambda m: m.get("card", {}).get("points") == base_points * 2)

        await host.send(json.dumps({"action": "resolve", "success": True}))
        next_host = await receive_until(host, lambda m: m.get("round_index") == 1)
        next_phone = await receive_until(phone, lambda m: m.get("round_index") == 1)
        assert next_host["scores"] == next_phone["scores"]
        assert next_host["scores"][0] == doubled["card"]["points"]
        print(f"PASS room={code} synchronized_score={next_host['scores']}")


if __name__ == "__main__":
    asyncio.run(main())
