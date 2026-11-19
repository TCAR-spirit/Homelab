# Twingate — Remote Access (ZTNA)

**Last updated:** 2026-11-19
**Status:** Live and verified from an outside network

How I reach the Command Center lab from outside the house — the laptop, the
phone, anywhere — **without opening a single inbound port on the firewall.**
Written down because remote access is a prerequisite for almost everything
else (managing Proxmox, SSH to the agents box, the D&D/Obsidian agents), and
because the troubleshooting story here is worth keeping: most of a day's
confusion came from testing against the *wrong door*, not a broken setup.

> This is my ZTNA (Zero Trust Network Access) layer. The short version of why
> it matters: a normal "reach my lab from a coffee shop" setup means port-
> forwarding through OPNsense — a permanent hole the whole internet can scan.
> Twingate needs **zero** open inbound ports. That tradeoff is the entire point.

---

## 1. The mental model (in plain terms)

**Twingate is not a VPN.** It does not put my laptop "onto" the home network.
It's a smart, per-app doorman: when a program on my device tries to reach a
*specific* home machine I've been authorized for, Twingate quietly builds a
private encrypted tunnel to **just that one machine, on that one connection** —
and everything else (Google, Netflix) keeps using the normal internet as if
Twingate weren't running. That's "split tunneling."

- **VPN** = "you are now inside the house."
- **Twingate** = "a specific door opens for a specific person reaching for a
  specific room, and closes behind them."

### The four components (and which are mine)

| Component | Where it lives | Job |
|-----------|---------------|-----|
| **Client** | My device (phone, laptop) | Watches for connections to my protected resources; opens the tunnel. Does nothing when I'm browsing normal sites. |
| **Connector** | *Inside* my LAN, behind OPNsense | The inside end of every tunnel. Makes **outbound-only** connections to Twingate — never listens for inbound. |
| **Controller** | Twingate cloud | The bouncer. Decides *if* I'm allowed; hands my Client a signed list (ACL) of what I may reach. Never touches my actual traffic. |
| **Relay** | Twingate cloud | The introducer. Helps Client and Connector find each other and shake hands. Cannot read my traffic (end-to-end encrypted). |

**Control plane vs. data plane** — the single most useful idea for debugging:
the Controller decides *if* a connection is allowed (control plane); the
Client + Connector + Relay decide *how* the bytes flow (data plane). When
something breaks, the first question is always: **is this a permission problem
(Controller) or a connectivity problem (Connector/network)?** That one question
narrows almost everything.

### Why no open ports

The Connector dials **out** to Twingate and keeps that connection alive. When
my laptop wants in, both sides were already "calling out," and the Relay
introduces them. So OPNsense stays fully closed from the outside — nothing to
scan, nothing to brute-force. Nobody reaches the *network*; they reach a single
*resource* I explicitly authorized. The Connector is a "narrow keyhole," not a
VPN gateway that drops you onto the LAN.

### A "Resource" = a specific host:port

In Twingate a **Resource** is just an address I told it to protect — e.g.
`192.168.10.47`, a name, or a whole range like `192.168.10.0/24`. Name and
address resolution happens **at the Connector, inside the house** — so from
outside I can type the *private* address of a home machine and it just works,
even though that address isn't routable from a coffee shop. **Resources +
Groups = the entire access model.** If I can see a resource but can't reach it,
it's almost always: (a) not defined as a Resource, or (b) my user isn't in a
Group granted that Resource.

---

## 2. My setup

- **Protected range:** `192.168.10.0/24` (the whole LAN), authorized to my user.
- **Clients in use:**
  - **Phone / Android (incl. ChromeOS):** installed from the Google Play Store.
    This is the Android client; it intercepts both Android-app traffic and —
    on my Chromebook — ChromeOS Chrome browser traffic. Confirmed working.
  - **Linux (Crostini / debian VM):** *not yet installed.* The planned
    long-term setup, because my real remote work (SSH, Hermes, the agents,
    editing the vault) happens in Linux, not in ChromeOS apps. A ChromeOS-only
    client leaves the Linux terminal blind when genuinely off-network.
- **Connector:** Shows **Connected / online** in the Twingate Admin Console.

### Live LAN map (discovered 2026-11-19)

| IP | Host | Open ports | Notes |
|----|------|-----------|-------|
| `192.168.10.1` | OPNsense (gateway/firewall) | 80, 443 | Firewall web UI |
| `192.168.10.2` | device w/ web UI | 80 | switch/AP (TBD) |
| `192.168.10.3` | device w/ web UI | 80, 443 | TBD |
| `192.168.10.11` | **debian VM** (Hermes / agents) | 22 | **SSH only — NOT Proxmox** |
| `192.168.10.47` | **Proxmox host** (M920q) | 8006, 22 | **the lab dashboard** |
| `192.168.10.103` | device | 22 | SSH host (TBD) |
| `192.168.10.148` | device | — | no scanned ports open |

> **The gotcha that cost us the afternoon:** `192.168.10.11` is the debian
> *guest VM* where Hermes runs — it only serves SSH (22). **Proxmox's web UI
> (8006) lives on the physical host at `192.168.10.47`, not on the VM.**
> Browsing to `.11:8006` gave "connection reset" — not a Twingate failure, but
> knocking on a port nothing was listening on. Correct URL:
> `https://192.168.10.47:8006`.

---

## 3. How to use it

There is **no "browse the network" screen** in the Twingate app. The app is
just the doorman standing in the background. To reach something, I open a normal
app and type the private address:

- **Proxmox web UI:** `https://192.168.10.47:8006` (accept the self-signed
  cert warning → proceed).
- **SSH to the agents box:** `ssh tristen@192.168.10.11` (from any SSH client;
  on a phone, an app like Termius — SSH is an app, not a browser).
- **Anything else on the LAN:** its own `192.168.10.x` address.

---

## 4. Verifying connectivity (the real test)

A test only counts if the device is genuinely **outside** the firewall
(cellular / a different network — not home Wi-Fi, and not a box that already
has a LAN path). Steps that actually prove the tunnel:

1. **Be off-network.** Phone on cellular, or laptop on a foreign Wi-Fi.
2. **Confirm the Connector is online** — Twingate Admin Console → Remote
   Networks → your network → Connector shows a green **Connected** dot.
3. **Hit a real, listening resource:** open `https://192.168.10.47:8006`.
   Expect the Proxmox login screen (after the cert warning). Reaching a
   private LAN host through a closed firewall from outside = the whole chain
   working.
4. **The decisive proof — toggle test:** turn Twingate **OFF** and reload.
   It should **fail** (can't reach a private IP from the public internet).
   Turn Twingate **ON** → it loads again. If OFF fails and ON works, the
   tunnel is unambiguously doing the work — not some other path.

> **Verified 2026-11-19:** from an outside network, `https://192.168.10.47:8006`
> loaded the Proxmox login (in both Android Firefox and ChromeOS Chrome). With
> Twingate OFF the connection failed; with it ON it loaded. Confirmed working.

### Reading failures

| Symptom | Likely meaning |
|---------|---------------|
| "This site can't be reached" / hangs | Traffic never entered the tunnel (client not intercepting / wrong client layer) **or** no route at all. |
| "Connection reset" | Tunnel **worked** and delivered you to the LAN host — but nothing was listening on that port (wrong host:port). |
| Loads with Twingate ON, fails with it OFF | Correct behavior — the tunnel is doing the work. |
| Can see the resource in-app but can't connect | Permission (control plane): not defined as a Resource, or not in an authorizing Group. |

---

## 5. Status & next steps

- **Done:** Android/ChromeOS client working; connector online; whole-LAN range
  authorized; end-to-end verified from outside with the OFF/ON toggle test.
- **Next:** install the **Twingate Linux client inside Crostini / on the debian
  VM** so SSH + Hermes + the agents tunnel properly when truly remote (the
  ChromeOS client doesn't cover Linux-container traffic).
- **Later:** define tighter per-resource entries + Groups instead of the broad
  `/24` (least privilege), once more agents and services come online.

---

*Why this doc exists (portfolio note): being able to explain the ZTNA tradeoff
— no inbound ports, resource-level access, control vs. data plane — and to
methodically debug it (resource = host:port; verify with an OFF/ON toggle from
a genuinely external network) is exactly the hands-on networking signal this
lab is meant to demonstrate.*
