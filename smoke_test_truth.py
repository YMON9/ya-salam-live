"""End-to-end test for حقيقة ولا خيال."""
import asyncio, json, websockets
URL="ws://127.0.0.1:8000/ws"
async def send(ws,action,**data): await ws.send(json.dumps({"action":action,**data},ensure_ascii=False))
async def state(ws):
    while True:
        d=json.loads(await ws.recv())
        if d.get("type")=="state": return d
async def main():
    sockets=[]
    host=await websockets.connect(URL);sockets.append(host);await send(host,"create",name="شهد");w=json.loads(await host.recv());code=w["room"];await state(host)
    for name in ("ريم","نور"):
        ws=await websockets.connect(URL);sockets.append(ws);await send(ws,"join",room=code,name=name);await ws.recv();await state(ws)
        for old in sockets[:-1]:await state(old)
    await send(host,"set_mode",mode="truth");states=[await state(x) for x in sockets]
    await send(host,"start",rounds=5);states=[await state(x) for x in sockets]
    assert all(x["truth"]["stage"]=="submit" for x in states)
    for i,ws in enumerate(sockets):
        await send(ws,"submit_truths",statements=[f"حقيقة أولى {i}",f"خيال واضح {i}",f"حقيقة ثانية {i}"],lie_index=1)
        states=[await state(x) for x in sockets]
    assert all(x["truth"]["stage"]=="guess" for x in states)
    assert all(x["truth"]["owner_id"] is None for x in states)
    owner_idx=next(i for i,x in enumerate(states) if x["truth"]["is_yours"])
    for i,ws in enumerate(sockets):
        if i!=owner_idx:
            await send(ws,"vote_truth",choice=1);states=[await state(x) for x in sockets]
    assert all(x["truth"]["stage"]=="reveal" for x in states)
    assert all(x["truth"]["lie_index"]==1 and x["truth"]["owner_id"] for x in states)
    assert sum(states[0]["personal_scores"].values())==2
    await send(host,"next_truth");states=[await state(x) for x in sockets]
    assert all(x["truth"]["stage"]=="guess" for x in states)
    print(f"PASS room={code} anonymous=true auto_reveal=true scoring=true next=true")
    for ws in sockets: await ws.close()
asyncio.run(main())
