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
    async with (
        websockets.connect(URL) as host,
        websockets.connect(URL) as opponent,
        websockets.connect(URL) as teammate,
    ):
        await host.send(json.dumps({"action": "create", "name": "المضيف"}))
        welcome = await receive_until(host, lambda m: m.get("type") == "welcome")
        code = welcome["room"]
        await receive_until(host, lambda m: m.get("type") == "state")

        await opponent.send(json.dumps({"action": "join", "room": code, "name": "الخصم"}))
        await receive_until(opponent, lambda m: m.get("type") == "welcome")
        joined = await receive_until(opponent, lambda m: m.get("type") == "state")
        assert len(joined["players"]) == 2
        await receive_until(host, lambda m: m.get("type") == "state" and len(m["players"]) == 2)

        await teammate.send(json.dumps({"action": "join", "room": code, "name": "زميل المضيف"}))
        teammate_welcome = await receive_until(teammate, lambda m: m.get("type") == "welcome")
        teammate_id = teammate_welcome["player_id"]
        await receive_until(teammate, lambda m: m.get("type") == "state" and len(m["players"]) == 3)
        await receive_until(host, lambda m: m.get("type") == "state" and len(m["players"]) == 3)
        await receive_until(opponent, lambda m: m.get("type") == "state" and len(m["players"]) == 3)

        await host.send(json.dumps({"action": "start", "rounds": 8}))
        host_game = await receive_until(host, lambda m: m.get("phase") == "game")
        opponent_game = await receive_until(opponent, lambda m: m.get("phase") == "game")
        teammate_game = await receive_until(teammate, lambda m: m.get("phase") == "game")
        assert host_game["room"] == opponent_game["room"] == teammate_game["room"] == code
        assert host_game["card"]["prompt"] is None

        await host.send(json.dumps({"action": "reveal"}))
        host_reveal = await receive_until(host, lambda m: m.get("revealed") is True)
        opponent_reveal = await receive_until(opponent, lambda m: m.get("revealed") is True)
        teammate_reveal = await receive_until(teammate, lambda m: m.get("revealed") is True)
        assert host_reveal["card"]["prompt"] == opponent_reveal["card"]["prompt"]
        assert teammate_reveal["card"]["prompt"] is None
        assert teammate_reveal["can_see_answer"] is False
        assert host_reveal["deadline"] == opponent_reveal["deadline"] == teammate_reveal["deadline"]

        await host.send(json.dumps({"action": "pause"}))
        paused = await receive_until(host, lambda m: m.get("paused_remaining") is not None)
        await receive_until(opponent, lambda m: m.get("paused_remaining") is not None)
        await receive_until(teammate, lambda m: m.get("paused_remaining") is not None)
        assert paused["deadline"] is None

        await host.send(json.dumps({"action": "resume"}))
        resumed = await receive_until(host, lambda m: m.get("deadline") is not None)
        await receive_until(opponent, lambda m: m.get("deadline") is not None)
        await receive_until(teammate, lambda m: m.get("deadline") is not None)
        assert resumed["paused_remaining"] is None

        before_extra = resumed["deadline"]
        await host.send(json.dumps({"action": "power", "power": "time"}))
        extra = await receive_until(host, lambda m: m.get("powers", [{}, {}])[0].get("time") is False)
        await receive_until(opponent, lambda m: m.get("powers", [{}, {}])[0].get("time") is False)
        await receive_until(teammate, lambda m: m.get("powers", [{}, {}])[0].get("time") is False)
        assert 14.9 <= extra["deadline"] - before_extra <= 15.1

        base_points = host_reveal["card"]["points"]
        await host.send(json.dumps({"action": "power", "power": "double"}))
        doubled = await receive_until(host, lambda m: m.get("card", {}).get("points") == base_points * 2)
        await receive_until(opponent, lambda m: m.get("card", {}).get("points") == base_points * 2)
        await receive_until(teammate, lambda m: m.get("card", {}).get("points") == base_points * 2)

        await host.send(json.dumps({"action": "resolve", "success": True}))
        next_host = await receive_until(host, lambda m: m.get("round_index") == 1)
        next_opponent = await receive_until(opponent, lambda m: m.get("round_index") == 1)
        await receive_until(teammate, lambda m: m.get("round_index") == 1)
        assert next_host["scores"] == next_opponent["scores"]
        assert next_host["scores"][0] == doubled["card"]["points"]

        await host.send(json.dumps({"action": "reveal"}))
        await receive_until(host, lambda m: m.get("round_index") == 1 and m.get("revealed"))
        await receive_until(opponent, lambda m: m.get("round_index") == 1 and m.get("revealed"))
        await receive_until(teammate, lambda m: m.get("round_index") == 1 and m.get("revealed"))
        await host.send(json.dumps({"action": "resolve", "success": False}))
        third_host = await receive_until(host, lambda m: m.get("round_index") == 2)
        await receive_until(opponent, lambda m: m.get("round_index") == 2)
        await receive_until(teammate, lambda m: m.get("round_index") == 2)
        assert third_host["current_team"] == 0
        assert third_host["active_player_id"] == teammate_id
        print(f"PASS room={code} hidden_answer=true rotation=true pause=true extra_time=true score={next_host['scores']}")


if __name__ == "__main__":
    asyncio.run(main())
