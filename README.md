# CASES21 automation

Lets a cloud AI agent operate a Windows app on a school PC through Power Automate.
Phase A targets a stand-in purchase order screen with fake data. CASES21 itself
(Phase B) needs principal and DE sign-off first.

## How it works

```
agent (cloud)                Power Automate (DE tenant)               school PC (AS-PC12EDTF)
-------------                --------------------------               -----------------------
bridge/pa.py  --HTTPS+token-->  cloud flow "cases21-bridge"   --->   desktop flow "cases21-hands"
              <--202, poll----   (HTTP trigger, async reply)  <---    focus window, send keys /
              <--screenshot---                                        clicks, screenshot (JPG)
```

1. `pa.py` gets an Entra token for the `cases21-bridge-agent` app and POSTs a list of steps.
2. The cloud flow replies 202 at once, runs the desktop flow (attended) and returns its result to the poll.
3. The desktop flow only touches a window whose title starts with `CASES21 stand-in`; it sends keystrokes
   and clicks, then returns a screenshot. The agent reads the screenshot and decides the next steps.

Step types: `{"type": "keys", "value": "ACME01{Tab}"}`, `{"type": "click", "x": 100, "y": 200}`,
`{"type": "wait", "value": 2}`.

## Status (Phase A)

| Gate | Result |
|---|---|
| Power Automate with school account | Works |
| HTTP trigger (Premium) | Works, on a 90-day Premium trial |
| PC registered for cloud-triggered desktop flows | Works (Windows 11 Education, admin rights) |
| Cloud flow runs a desktop flow | Not tested yet (`bridge-hello`) |
| Entra app registration for the agent | Not checked yet |
| End-to-end from the agent | Not tested yet |

## Layout

- `standin/po-entry.html` – fake CASES21 purchase order entry screen (draft field list; correct it to match the real one)
- `bridge/pa.py` – agent-side client; `bridge/test_pa.py` – its tests (`cd bridge && python3 -m unittest`)
- `docs/SETUP.md` – click-by-click setup for the flows, app registration and secrets

## Before Phase B (real CASES21)

- Written OK from the principal and DE: generative AI policy (school financial information is "sensitive"),
  Power Automate use, software on the CASES21 PC.
- CASES21 runs in Citrix, so the desktop flow can only use keys, clicks and screenshots unless DE installs
  the Power Automate agent for virtual desktops on its Citrix hosts.
- Screenshots of real CASES21 would send school data to the agent. Lock the desktop flow to fixed
  operations, keep payments and approvals out of scope, and keep a human confirm before any save.
- The trial ends after 90 days; ongoing use needs a Power Automate Premium licence.
