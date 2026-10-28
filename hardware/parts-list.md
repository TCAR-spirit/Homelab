# Parts List

Target budget: ~$1,450 · Phase 1 recorded spend: **$1,021.75**

Items marked **Acquired** show the actual price paid. Items still in planning
show rounded estimates. Several Phase 1 components were substituted during
purchasing — the original plan is noted where that happened, along with why.

---

## Acquired — Phase 1

| Item | Model | Paid | Date |
|------|-------|------|------|
| Proxmox host | HP EliteDesk 800 G4 Mini — i7-8700T, 32GB DDR4, 500GB SSD | $415.00 | 2026-09-29 |
| Cabling (initial) | CAT6 patch cables and keystone connectors | ~$40 (est.) | 2026-09-17 |
| Wireless AP | TP-Link Omada EAP720 — BE5000 Wi-Fi 7, 2.5G port, DC adapter | $99.99 | 2026-10-08 |
| Firewall | BOSGAME E5 Plus Mini PC — Ryzen 5 5400U, 8GB, 256GB SATA SSD, **dual 2.5G LAN** | $197.99 | 2026-10-20 → 25 |
| Switch | TP-Link Omada ES210X-M2 — 8× 2.5G, 2× 10G SFP+, managed | $99.99 | 2026-10-20 → 25 |
| Rack | Tecmojo 10" 9U mini server rack, 7.87" depth | $119.90 | 2026-10-20 → 25 |
| Shelves | GeeekPi 1U vented cantilever tray, 10" rack — 2 pack | $28.90 | 2026-10-20 → 25 |
| Power | Mifaso 12-outlet wall-mount surge protector | $12.99 | 2026-10-20 → 25 |
| Install media | Lexar D40E 128GB dual USB-A / USB-C | $29.99 | 2026-10-20 → 25 |
| Cabling (additional) | CAT6 patch cables | ~$17.00 | 2026-10-27 → 28 |

**Recorded total: $1,021.75** (plus the September cabling, which was not
itemized at the time)

### Substitutions from the original plan

| Planned | Purchased | Reason |
|---------|-----------|--------|
| DeskPi RackMate T2 12U — $160 | Tecmojo 9U — $119.90 | Cheaper, and 9U is sufficient for the Phase 1–4 device count |
| Lenovo ThinkCentre M710q (i7-6700T) + USB 2.5GbE adapter — $240 combined | BOSGAME E5 Plus — $197.99 | Dual **onboard** 2.5G NICs instead of a USB adapter on the WAN side. Cheaper than the combination, newer CPU, and no USB NIC as a single point of failure. Trade-off: Realtek NICs requiring vendor drivers (see troubleshooting) |
| Omada EAP650 — Wi-Fi 6 — $80 | Omada EAP720 — Wi-Fi 7 — $99.99 | BE5000 and a 2.5G uplink to match the switch. $20 for a generational jump |
| DeskPi 1U shelves ×3 — $60 | GeeekPi 1U vented ×2 — $28.90 | Vented cantilever trays, two were enough for the current load |
| Rack PDU — $50 | Mifaso surge strip — $12.99 | Interim. A proper rack PDU is deferred, not cancelled |

---

## Deferred

Planned but not yet purchased. These are quality-of-life and expansion items
rather than blockers — the lab is fully functional without them.

| Item | Model | Est. | Note |
|------|-------|------|------|
| Patch panel | GeeekPi 0.5U 12-port CAT6 keystone | $25 | Deferred — cable runs are short enough to dress directly for now |
| Rack PDU | 10" rack AC PDU w/ surge, 8 outlet | $50 | Deferred — surge strip covers current draw |
| Cooling | DeskPi 1U quad fan panel | $40 | Deferred — thermals not yet a problem at current density |
| RAM upgrade | 32GB DDR4 SO-DIMM (→ 64GB total) | $175 | Postponed — 32GB is ample until the agent containers are running |
| Storage | 1TB NVMe | $70 | Postponed — 475GB usable is not close to constrained |
| End table | 3-tier shelf for rack | $20 | Postponed |

---

## Later Phases

| Item | Model | Est. Price | Phase |
|------|-------|-----------|-------|
| Pi 5 8GB + mount | Raspberry Pi 5, rack mount, PSU | $110 | 3 |
| GPU node | Small-tower host for the existing RTX 3060 12GB — game server + local LLM inference | TBD | 3 |
| NAS box | Used OptiPlex SFF or N100 2-bay | $150 | 4 |
| NAS drives | 2× 4TB WD Red Plus / IronWolf | $180 | 4 |
| Backup drive | 8TB external USB | $130 | 4 |
