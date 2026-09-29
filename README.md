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

## Build Log

2026-07-17 — Zordon v0.1 running: Discord bot with LLM backend, containerized with Docker.

### 2026-09-29 — Proxmox host acquired
Purchased the HP [ProDesk 600 G4 / EliteDesk] Mini (i7-8700T, 32GB RAM,
NVMe SSD) as the Proxmox virtualization host — the first hardware
purchase of Phase 1. This box will run the core service stack:
the self-hosted Omada controller, Pi-hole, the AI agents, and the
portfolio site. Chosen for its 8th-gen 6-core CPU and 64GB RAM
ceiling, giving headroom for future local workloads.
