# Future Additions

Secondary projects to build on top of the core homelab once the main phases
are complete. These are not part of the baseline build — they are ideas I
want to pursue as the lab matures, listed roughly in order of interest.

Each entry notes what it depends on, so I can tell what has to exist first.

---

## 1. Morpher Communicator

A 3D-printed Power Rangers morpher converted into a voice interface for a
self-hosted AI assistant. Press the button, speak, and get a spoken reply
from the assistant running on the rack.

**How it works:** the morpher itself is only a shell containing a
microphone, a small speaker/amplifier, a button, and a wifi microcontroller
(ESP32 class). All processing happens on the homelab — audio is streamed to
the server, converted to text, passed to the self-hosted LLM, and the
response is converted back to speech and returned to the device.

**Planned capabilities:** daily schedule, weather, home network status,
reminders, and general assistant queries. A smart watch may be paired later
as a notification/display target rather than a voice input.

**Depends on:** self-hosted LLM running on the Proxmox host, a speech-to-text
and text-to-speech pipeline, and Home Assistant (or equivalent) for calendar,
weather, and device integrations.

**Skills demonstrated:** embedded hardware, 3D design and printing, audio
pipelines, self-hosted AI inference, home automation integration.

**Note:** personal-use build only — the morpher design is licensed IP and
will not be sold or distributed.

---

## 2. Home Assistant Integration

Self-hosted home automation as the bridge between the AI assistant and
real-world data — calendars, weather, network device status, and smart home
controls. Runs as a container on the Proxmox host.

**Depends on:** Phase 1 (Proxmox host).

**Skills demonstrated:** service self-hosting, API integrations, automation
scripting.

---

## 3. Network Monitoring and Dashboard

A monitoring stack for the lab — uptime checks, service health, bandwidth
usage, and alerting. Uptime Kuma for simple service monitoring, with the
option to add Grafana and Prometheus for metrics and dashboards.

**Depends on:** Phase 1 (network and Proxmox host).

**Skills demonstrated:** infrastructure monitoring, metrics collection,
dashboarding — all directly relevant to data center and NOC roles.

---

## 4. Network-Wide DNS Filtering

Pi-hole or AdGuard Home as a network-level DNS sinkhole, with DNS-over-HTTPS
upstream. Provides ad and tracker filtering for every device on the network
and gives visibility into what devices are actually talking to.

**Depends on:** Phase 1 (VLANs and firewall).

**Skills demonstrated:** DNS administration, network security, traffic
analysis.

---

## 5. 3D Print Farm Management

A self-hosted print server (OctoPrint or Klipper/Mainsail) to manage prints,
monitor jobs remotely, and keep a library of my own STL designs. Ties
directly into the STL files I design and sell.

**Depends on:** Phase 1 (network), a Raspberry Pi or spare mini PC.

**Skills demonstrated:** Linux service administration, remote device
management.

---

## 6. STL Portfolio Gallery

A gallery section of the portfolio site showcasing my 3D designs, with
renders, print settings, and links out to the storefront where they are
sold. Hosted alongside the main portfolio site.

**Depends on:** Phase 2 (portfolio site).

**Skills demonstrated:** web development, content management.

---

## 7. Automated Backup Pipeline

Scheduled, verified, offsite-capable backups for the lab: VM snapshots from
Proxmox, container volumes, configuration exports, and NAS data. Follows the
3-2-1 backup rule with restore testing, not just backup creation.

**Depends on:** Phase 4 (NAS).

**Skills demonstrated:** backup and disaster recovery planning, scripting,
storage management.

---

## 8. Game Server Hosting

Self-hosted game servers for my group — Minecraft, Foundry VTT for D&D
sessions, or similar — running as containers with proper resource limits and
secured remote access through Twingate rather than exposed ports.

**Depends on:** Phase 1 (Proxmox host), Phase 2 (Twingate).

**Skills demonstrated:** container resource management, secure remote access,
service administration.

---

## 9. Network Asset Inventory Tool

A small self-hosted application to track hardware in the lab — devices,
specs, IP assignments, purchase dates, and warranty status. A personal
version of the asset tracking work I do professionally, built to my own
specifications.

**Depends on:** Phase 1 (Proxmox host).

**Skills demonstrated:** Python development, database design, web
application deployment.

---

*This list will grow as the lab develops. Items may be promoted into the
main build phases if they become priorities.*
