"""End-to-end checks for emoji, imposter, lobby return, and room closure."""
import asyncio
import json
import websockets

URL = "ws://127.0.0.1:8000/ws"

async def recv_state(ws):
    while True:
        data = json.loads(await ws.recv())
        if data.get("type") == "state": return data

async def send(ws, action, **data):
    await ws.send(json.dumps({"action": action, **data}, ensure_ascii=False))

async def join_group(names):
    sockets=[]; states=[]
    host=await websockets.connect(URL); sockets.append(host)
    await send(host,"create",name=names[0]); welcome=json.loads(await host.recv()); code=welcome["room"]
    states.append(await recv_state(host))
    for name in names[1:]:
        ws=await websockets.connect(URL); sockets.append(ws); await send(ws,"join",room=code,name=name)
        await ws.recv(); states.append(await recv_state(ws))
        for old in sockets[:-1]: await recv_state(old)
    return code,sockets

async def main():
    code,s=await join_group(["شهد","ريم","سارة","نور"]); host=s[0]
    await send(host,"set_mode",mode="emoji"); states=[await recv_state(x) for x in s]
    await send(host,"start",rounds=5); states=[await recv_state(x) for x in s]
    assert all(x["emoji"]["answer"] is None for x in states)
    await send(s[1],"submit_guess",guess="تجربة"); states=[await recv_state(x) for x in s]
    assert all(not x["emoji"]["guesses"] for x in states)
    for i, ws in enumerate((s[0], s[2], s[3])):
        await send(ws,"submit_guess",guess=f"تخمين {i}")
        states=[await recv_state(x) for x in s]
    assert all(x["emoji"]["answer"] for x in states)
    assert len(states[0]["emoji"]["guesses"]) == 4
    await send(host,"award_guess",player_id=states[1]["you"]); states=[await recv_state(x) for x in s]
    assert states[0]["personal_scores"][states[1]["you"]] == 1
    await send(host,"return_lobby"); states=[await recv_state(x) for x in s]; assert all(x["phase"]=="lobby" for x in states)
    await send(host,"set_mode",mode="imposter"); states=[await recv_state(x) for x in s]
    await send(host,"set_imposter",category="دولة",count=1); states=[await recv_state(x) for x in s]
    await send(host,"start",rounds=5); states=[await recv_state(x) for x in s]
    imposters=[x for x in states if x["imposter"]["your_role"]=="imposter"]
    assert len(imposters)==1 and imposters[0]["imposter"]["word"] is None
    assert all(x["imposter"]["word"] for x in states if x not in imposters)
    await send(host,"reveal_imposters"); states=[await recv_state(x) for x in s]
    imp=next(x for x in states if x["imposter"]["your_role"]=="imposter")
    assert len(imp["imposter"]["options"])==4
    imp_ws=s[states.index(imp)]; choice=imp["imposter"]["options"][0]
    await send(imp_ws,"submit_imposter_choice",choice=choice); states=[await recv_state(x) for x in s]
    imp_after=next(x for x in states if x["imposter"]["your_role"]=="imposter")
    assert imp_after["imposter"]["selected_choice"] == choice
    assert imp_after["imposter"]["choice_correct"] in (True, False)
    await send(host,"reveal_imposter_answer"); states=[await recv_state(x) for x in s]
    assert all(x["imposter"]["answer_revealed"] for x in states)
    await send(host,"close_room")
    closed=[json.loads(await x.recv()) for x in s]
    assert all(x["type"]=="room_closed" for x in closed)
    print(f"PASS room={code} emoji_hidden=true guesses=true imposter_private=true options=4 close_room=true")

asyncio.run(main())
