# Firewall Rules — OPNsense

**Last verified:** 2026-11-04
**Scope:** flat LAN, pre-VLAN. Inter-segment policy comes with VLAN
segmentation and will be added here.

The rules below are *egress* filtering — what this network's own devices are
allowed to do on the way out. Inbound is already handled by the default deny
on WAN.

---

## Baseline — what OPNsense gives you by default

Worth stating, because the defaults are stronger than they are usually given
credit for and it frames what the added rules are actually for.

| Interface | Default behavior |
|---|---|
| **WAN** | Default deny inbound. Nothing from the internet reaches the LAN without an explicit rule or port forward. None exist. |
| **LAN** | Automatic anti-lockout rule, then "Default allow LAN to any" — all outbound permitted. |

So the firewall arrives closed from the outside and wide open from the
inside. Egress filtering is the gap worth closing on a flat network.

---

## WAN interface settings

**Interfaces → WAN**

| Setting | State | Why |
|---|---|---|
| Block bogon networks | **Enabled** | Blocks traffic from address space that should never appear on the internet |
| Block private networks | **Disabled — deliberately** | See below |

### Why "Block private networks" must stay off here

This is standard hardening advice everywhere, and in this topology it would
sever the uplink entirely.

The lab is double-NATted: OPNsense's WAN sits on `192.168.1.0/24`, handed out
by the Verizon 5G router. That is itself RFC1918 private space, so enabling
"Block private networks" would cause the firewall to drop its own upstream
gateway.

Revisit this only if the Verizon router is ever put into bridge or
IP-passthrough mode and OPNsense holds a public address directly.

---

## Aliases

**Firewall → Aliases**

| Name | Type | Content | Used by |
|---|---|---|---|
| `SMB_Ports` | Port(s) | `137`, `138`, `139`, `445` | LAN rule 4 |

Aliases are named objects referenced by rules rather than literal values
scattered across them. One place to change, and a rule that reads
`SMB_Ports` says what it means where `137,138,139,445` has to be looked up.

---

## LAN rules

**Firewall → Rules → LAN**

Rules are evaluated **top to bottom, first match wins**. New rules are added
at the bottom of the list by default, which places them *below* "Default
allow LAN to any" — where a block rule can never fire. Each rule below had to
be moved above that default allow.

Order as applied:

| # | Action | Protocol | Source | Destination | Dest port | Log | Purpose |
|---|---|---|---|---|---|---|---|
| — | *(auto)* | — | — | — | — | — | Anti-lockout — guarantees web UI access from LAN |
| 1 | Pass | TCP/UDP | LAN net | This Firewall | 53 | — | Permit DNS to the firewall's own resolver |
| 2 | Block | TCP/UDP | LAN net | any | 53 | ✓ | Block all other DNS |
| 3 | Block | TCP | LAN net | any | 853 | ✓ | Block DNS-over-TLS |
| 4 | Block | TCP/UDP | LAN net | LAN net *(inverted)* | `SMB_Ports` | ✓ | Block SMB/NetBIOS leaving the network |
| — | Pass | any | LAN net | any | — | — | Default allow LAN to any (existing) |

### Rules 1–3 — forcing DNS through the firewall

Rule 1 must sit above rule 2, or the firewall blocks its own clients from
reaching it.

Devices routinely ignore the DNS server handed out by DHCP and talk directly
to a hardcoded public resolver — smart TVs and IoT hardware are the usual
offenders. On a network with no filtering this is merely untidy. Once Pi-hole
is in place it would mean those devices silently bypass every block list on
the network.

Building this now means Pi-hole works correctly from the moment it exists,
rather than appearing to work while leaking.

Rule 3 closes DNS-over-TLS, which is the same bypass on a different port.
DNS-over-HTTPS cannot be blocked by port, since it is indistinguishable from
ordinary HTTPS traffic — that needs a destination blocklist and is a
later problem.

### Rule 4 — SMB egress

SMB (Server Message Block) is Windows file and printer sharing: ports 137–139
for legacy NetBIOS, 445 for the modern protocol.

It has no business leaving the network. A crafted link can induce Windows to
open an SMB connection to an external host, leaking hashed credentials in the
handshake. Blocking it outbound closes that off at no cost.

The **inverted** destination is what makes this work: "anywhere except this
LAN." Internal file sharing to the Proxmox host and between workstations is
unaffected; only traffic leaving the network is dropped.

---

## Known trade-off

Chromecast and some Google devices hardcode `8.8.8.8` and will fail outright
against rule 2 rather than falling back.

If that surfaces, the gentler approach is a **NAT redirect** instead of a
block — Firewall → NAT → Port Forward, redirecting LAN-sourced port 53 to the
firewall. That transparently rewrites the destination rather than denying it,
so the device keeps working and still gets filtered answers.

Not currently needed; recorded in case a device starts misbehaving.

---

## Verifying

**Firewall → Log Files → Live View**, filtered to the LAN interface.

Rules 2–4 log, so hits appear here. Worth watching for a while after any
change — it also reveals which devices had been quietly using outside DNS.

---

## Deferred to VLAN segmentation

These need segments to exist before they can be written meaningfully:

- Inter-VLAN policy — which segments may initiate to which
- IoT isolation — internet access, no access to trusted hosts
- Guest network — internet only, no lateral access at all
- Restricting firewall and Proxmox management to a management segment or
  specific hosts
- Suricata IDS/IPS — on a flat network it generates alerts with no
  segmentation context to act on
