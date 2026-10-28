# Homelab

A running log for the development of my home lab and home network.

This is my first major personal IT project. The goal is to build a
successful and diverse home lab that serves multiple purposes:

- **Rack and stack experience** — building out a miniature 10" rack
  with enterprise-style organization (patch panel, PDU, cable management)
- **Network security** — a dedicated OPNsense firewall monitoring
  traffic flow, with VLAN segmentation and least-privilege access rules
- **Self-hosted portfolio site** — a server hosting my IT portfolio
  and project write-ups
- **Zero trust access** — Twingate for secure remote access to
  internal services
- **Self-hosted AI** — Hermes as a locally hosted AI framework serving
  as an assistant for my network and personal projects. Long-term goal:
  a voice-capable D&D assistant that transcribes sessions, helps with
  world and lore building, and summarizes each session for the next one
- **NAS** — network storage and backups

I'll add to this as the build progresses and as my curiosity grows,
but this is the baseline for my personal network rack.

## Current State

**Phase 1 foundation is complete.** Verizon 5G router → OPNsense firewall →
Omada 2.5G switch → Proxmox host, two workstations, and an access point
awaiting configuration.

![Home network topology](network/home-network-topology.png)

| | |
|---|---|
| **Operational reference** | [`network/current-state.md`](network/current-state.md) — addressing, port map, host inventory, next steps |
| **Phase plan** | [`ROADMAP.md`](ROADMAP.md) — what each phase delivers and what it depends on |
| **Hardware and spend** | [`hardware/parts-list.md`](hardware/parts-list.md) |
| **Troubleshooting log** | [`troubleshooting/`](troubleshooting/) |
| **AI design decisions** | [`docs/ai-architecture.md`](docs/ai-architecture.md) — model routing, cost controls, agent architecture |
| **Later ideas** | [`future-additions.md`](future-additions.md) |

## Build Log

2026-07-17 — Zordon v0.1 running: Discord bot with LLM backend, containerized with Docker.

### 2026-09-17 — Cabling and connectors acquired
Picked up the bulk of the network cabling — CAT6 patch cables and
connectors — ahead of the compute hardware. Getting cabling in early
so that once the switch and hosts arrive, runs can be measured and
dressed cleanly rather than retrofitted.

### 2026-09-29 — Proxmox host acquired
Purchased an HP EliteDesk 800 G4 Mini (i7-8700T, 32GB RAM, 500GB NVMe)
as the Proxmox virtualization host — the first hardware purchase of
Phase 1. This box will run the core service stack: the self-hosted
Omada controller, Pi-hole, the AI agents, and the portfolio site.
Chosen for its 8th-gen 6-core CPU and 64GB RAM ceiling, giving
headroom for future local workloads.

### 2026-10-08 — Wireless access point acquired
Bought an Omada EAP720 (BE5000 Wi-Fi 7, 2.5G uplink) rather than the EAP650
Wi-Fi 6 model originally planned — $20 for a generational jump and an uplink
that matches the switch. Chose the DC-adapter variant deliberately: the
ES210X-M2 is not a PoE switch, so the AP has to be powered locally.

### 2026-10-20 → 10-25 — Core Phase 1 hardware acquired
Rack, firewall, switch, shelves, power, and install media. Two substitutions
from the original plan, both recorded with reasoning in the
[parts list](hardware/parts-list.md):

- **Firewall:** a BOSGAME E5 Plus (Ryzen 5 5400U, dual *onboard* 2.5G NICs)
  instead of a Lenovo M710q plus a USB 2.5GbE adapter. Cheaper than the
  combination, newer CPU, and no USB NIC as a single point of failure. The
  trade-off is Realtek NICs that need a vendor driver.
- **Rack:** a Tecmojo 10" 9U instead of the DeskPi RackMate T2 12U. Cheaper,
  and 9U covers the Phase 1–4 device count.

### 2026-10-22 — OPNsense: Realtek NIC drivers installed
Installed the `os-realtek-re` vendor driver package to bring up the 2.5G
interfaces. With no interfaces assigned yet the box had no network access,
so the package had to come in over USB — which turned into the real problem.
Three layers of it: a comma in a FreeBSD device path that was actually a
delimiter between two device nodes, an exFAT-formatted drive that FreeBSD
cannot mount at all, and the discovery that the 32GB FAT32 ceiling is a
limitation of the Windows format dialog rather than the filesystem.

Full write-up: [Incident 1](troubleshooting/phase1-buildout-oct-2026.md).

### 2026-10-25 — Proxmox VE 9.2 installed
Installed to the EliteDesk's 500GB SATA SSD (~475GB usable) on ext4.

Getting there took longer than the install itself. The ISO had been copied
onto the USB drive as a file rather than written to it — Proxmox ships a
hybrid ISO that has to be written in Rufus's DD Image mode. Then the HP
firmware would not register F9 or F10, because Fast Boot and a Startup Delay
of zero left no window for a USB keyboard to initialize. And underneath both
of those: the keyboard itself did not work before an OS loaded. One bad
keyboard produced symptoms that looked like three separate firmware faults.

Also caught the installer defaulting the timezone to `America/Adak` at the
confirmation screen — nine hours off, and every log timestamp, cron
schedule, and backup window on the host would have inherited it.

Full write-up: [Incident 2](troubleshooting/phase1-buildout-oct-2026.md).

### 2026-10-26 → 10-28 — Rack assembly and cabling
Assembled the 9U rack and mounted the firewall, switch, and Proxmox host on
vented 1U trays. Additional CAT6 patch cables to finish the runs. Patch
panel, rack PDU, and fan panel deferred — short runs dress cleanly without a
panel, and thermals are not a concern at current density.

### 2026-10-27 — Network integration and subnet migration
Wired the rack in and hit a subnet collision: OPNsense's default LAN
(`192.168.1.1/24`) overlapped the Verizon 5G router's own
`192.168.1.0/24`. Caught it before power-on by checking the upstream subnet
rather than after, which saved the confusing part.

Migrated the LAN to `192.168.10.0/24`, re-addressing the Proxmox host
**first** so it would not be stranded on a subnet that no longer existed.
Along the way: a link that was up with no DHCP (the switch uplink was in the
WAN port, not LAN), and the discovery that OPNsense 26.7 serves DHCP through
Dnsmasq rather than the ISC DHCPv4 path most guides still reference.

Full write-up: [Incident 3](troubleshooting/phase1-buildout-oct-2026.md).

### 2026-10-28 — Phase 1 foundation complete
Routed, segmented network running end to end: Verizon 5G router → OPNsense →
Omada 2.5G switch → Proxmox host and both workstations. DHCP and DNS served
from the firewall, Proxmox reachable on its management address, enterprise
repository swapped to no-subscription.

Remaining before Phase 2: the Omada controller container, AP adoption, and
Pi-hole. Current state documented in
[`network/current-state.md`](network/current-state.md).
