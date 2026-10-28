# Roadmap

The build is organized into phases. Each phase has a clear completion
condition, and later phases depend on earlier ones being stable rather than
merely finished.

Phases are referenced by number throughout the
[parts list](hardware/parts-list.md) and
[future additions](future-additions.md).

---

## Phase 1 — Rack and network foundation

**Status: complete** (2026-10-28)

The physical and logical foundation everything else sits on: a dedicated
firewall, a managed switch, wireless coverage, and a virtualization host.

| | |
|---|---|
| **Delivered** | 9U rack assembled · OPNsense firewall routing and serving DHCP/DNS · Omada 2.5G managed switch · Proxmox VE 9.2 host · both workstations wired |
| **Remaining** | Omada controller container · AP adoption · Pi-hole · VLAN segmentation |
| **Completion condition** | A routed, segmented network with centrally managed switching and wireless, DNS filtering in place, and a hypervisor ready to take workloads |

Current operational detail: [`network/current-state.md`](network/current-state.md)

---

## Phase 2 — Remote access and portfolio

**Status: not started**
**Depends on:** Phase 1

Zero-trust remote access and the first externally visible service.

| | |
|---|---|
| **Scope** | Twingate for remote access to internal services without exposing ports · self-hosted portfolio site and project write-ups · reverse proxy with TLS |
| **Blocker to resolve** | The lab is currently double-NATted behind the ISP router. This needs addressing before inbound connections work cleanly |
| **Completion condition** | Internal services reachable from outside the house without a port forward, and the portfolio site serving publicly |

---

## Phase 3 — Compute expansion and AI groundwork

**Status: not started**
**Depends on:** Phase 1

Adds the compute to run agent workloads and, eventually, local inference.

| | |
|---|---|
| **Scope** | Hermes agent harness on a Proxmox VM · containerized agents with least-privilege scoping · Raspberry Pi 5 node · GPU node built around the existing RTX 3060 12GB, serving as both game server and local inference host |
| **Design decisions** | [`docs/ai-architecture.md`](docs/ai-architecture.md) |
| **Completion condition** | Agents running in production against real tasks, with per-agent token metering, and a local inference path available for routine traffic |

---

## Phase 4 — Storage and backup

**Status: not started**
**Depends on:** Phase 1, Phase 3 (GPU/storage node)

| | |
|---|---|
| **Scope** | NAS host with mirrored drives · media and project storage · automated Proxmox VM snapshot backups · 3-2-1 backup policy with restore testing, not just backup creation |
| **Completion condition** | Scheduled, verified backups of VMs, container volumes, and configuration, with at least one tested restore |

---

## Phase 5 — Voice D&D assistant

**Status: prototype running** (Zordon v0.1, 2026-07-17)
**Depends on:** Phase 3, Phase 4

The long-horizon goal the rest of the lab was partly built to support.

| | |
|---|---|
| **Scope** | Joins Discord voice sessions and captures audio · transcribes sessions locally · produces session notes and recaps · assists with next-session prep and lore continuity · speaks responses in a distinct voice |
| **Current state** | v0.1 is a Discord bot responding to `!ask` with an LLM backend, running in Docker. Voice capture, transcription, and TTS are all unbuilt |
| **Hardest part** | Discord voice *receiving* — library support is the integration risk, not the AI |
| **Completion condition** | A session can be recorded, transcribed, and summarized end to end without manual steps |

Architecture: [`docs/ai-architecture.md`](docs/ai-architecture.md)

---

## Ordering principle

Phases are ordered so that each one is useful on its own and makes the next
one easier, rather than building toward a payoff that only arrives at the
end. The foundation came first because everything is harder to retrofit onto
an unsegmented network; monitoring comes before agents because alerting
needs something to alert on; storage comes before the assistant because
session audio has to live somewhere.

Items from [future additions](future-additions.md) may be promoted into a
phase if they become priorities.
