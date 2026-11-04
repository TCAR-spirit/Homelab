# Omada Controller — LXC Build and Troubleshooting

**Date:** 2026-10-29
**Host:** Proxmox `pve` · Container 100 (`omada`)

## Goal

Run the Omada Network Application self-hosted on the Proxmox host as the
single pane of glass for the ES210X-M2 switch and the EAP720 access point,
rather than managing them standalone from the phone app.

## Decisions

**LXC container, not a VM.** The controller needs roughly 2GB. In an LXC that
is 2GB actually consumed; in a VM it is 4GB allocated whether used or not. On
a 32GB host with Pi-hole, a reverse proxy, monitoring, and a Hermes VM still
to come, that difference is most of the memory budget. A VM would only be
warranted for kernel isolation or a clean Docker host, and the controller
installs natively on Debian.

**Manual install, not a community helper script.** The helper scripts build
the whole thing in about five minutes, but they run as root and were not
written here. Installing Java, MongoDB, and the `.deb` by hand takes longer
and means the dependency chain is understood when something breaks.

**Adoption order matters.** Omada devices can be managed *either* standalone
from the phone app *or* by a controller — never both. A device adopted
standalone must be factory reset before it will join a controller, so the
controller was stood up first and devices adopted into it once.

## Container specification

| | |
|---|---|
| Template | `debian-12-standard` |
| CT ID / hostname | `100` / `omada` |
| Privilege | unprivileged |
| Cores | 2 |
| Memory | **4GB RAM / 1GB swap** (revised up from 2GB/512MB — see below) |
| Disk | 16GB |
| Network | static `192.168.10.10/24`, gateway `192.168.10.1`, DNS `1.1.1.1` |

**The static address is not optional.** The controller's address is written
into every device it adopts. If it moves, every adopted device is orphaned.
`.10` sits in the `2–99` infrastructure range, outside the DHCP pool.

## Issues encountered

### 1. `tpeap: command not found`

`tpeap start` was run before the controller package was installed. `tpeap` is
the control script that ships *with* the `.deb` — it does not exist until the
package is on disk.

*Fix:* install the package first, then use `tpeap`.

### 2. The product has been renamed

Most documentation, and most forum answers, refer to **Omada SDN
Controller** and filenames matching `Omada_SDN_Controller_*.deb`. The current
download is named **Omada Network Application**:

```
Omada_Network_Application_v6.3.0.45_linux_x64_20260903171910.deb
```

Any glob or copy-pasted command built around the old name silently matches
nothing.

### 3. Java version depends on the controller version

| Controller version | Java required |
|---|---|
| v6.4.0 and later | OpenJDK 21 |
| v5.15.20 – v6.3.x | OpenJDK 17 or 21 |
| before v5.15.20 | OpenJDK 8 or 11 |

Debian 12 ships OpenJDK **17**, not 21. A v6.4.0+ controller therefore needs
OpenJDK 21 pulled from `bookworm-backports`, while anything in the 5.15.20 –
6.3.x band works with the default.

**The version is in the `.deb` filename**, so the correct order is: download
first, read the version, *then* install the matching Java. This build landed
on v6.3.0.45, so the Debian 12 default was sufficient and backports were not
needed.

To read the version out of a package already downloaded:

```bash
dpkg-deb -f Omada_Network_Application_*.deb Package Version
```

### 4. Placeholder brackets pasted into the shell

```bash
wget "<https://static.tp-link.com/...deb>"     # rejected — invalid URL
wget "https://static.tp-link.com/...deb"       # correct
```

The angle brackets were documentation markers, not part of the command. Inside
quotes they are not shell redirection, so the shell passes them through and
`wget` rejects the whole string as a malformed URL rather than failing on
syntax.

### 5. MongoDB is not in the Debian repositories

Licensing. It comes from MongoDB's own apt repository:

```bash
curl -fsSL https://pgp.mongodb.com/server-8.0.asc \
  | gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor

echo "deb [signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" \
  > /etc/apt/sources.list.d/mongodb-org-8.0.list

apt update && apt install -y mongodb-org
systemctl enable --now mongod
```

MongoDB 5.0 and later require **AVX** CPU support. The i7-8700T has AVX2, so
this was not a problem here — but a `mongod` that dies instantly on start is
usually this.

### 6. 2GB of RAM was not enough — the real failure

After installation the web UI at `https://192.168.10.10:8043` returned a page
whose tab title and favicon were correct, but whose body never rendered. This
looked like a slow first-run initialization: the controller *was* responding,
so the service was clearly alive.

It was not slow. It was out of memory.

```
Memory   98.99%  (1.98 GiB of 2.00 GiB)
SWAP     99.96%  (511.82 MiB of 512.00 MiB)
```

Both exhausted, with CPU pinned around 35% — the signature of thrashing
rather than work. The controller's Java process takes roughly a 1GB heap,
MongoDB wants another 0.5–1GB, and the OS needs the rest. First-run
initialization builds the database schema, which is the most memory-hungry
thing the controller ever does, so it failed precisely at the point of
highest demand.

*Fix:* raised the container to **4GB RAM and 1GB swap** in Proxmox
(Container 100 → Resources), then rebooted it. Initialization completed and
the web UI loaded normally.

**Why the diagnosis took a detour:** a served page with the right title is
strong evidence the service is healthy, which pointed at startup timing
rather than resources. The Proxmox container summary — with its memory and
swap bars both red — answered in one screen what log-reading had not.
Container-level metrics are worth checking before application logs when the
symptom is "slow or hanging" rather than "erroring".

## Outcome

Controller running. The ES210X-M2 switch is adopted and under management. The
EAP720 is powered and pulling DHCP but not yet adopted.

## Takeaways

- Check the resource graphs before the application logs when something hangs
  rather than errors. A container summary showing red memory and swap bars is
  a faster diagnosis than any amount of log tailing.
- A page that loads with the correct title and favicon proves the service is
  *reachable*, not that it is *working*. Reachable-but-blank is a backend
  problem, and resource exhaustion is high on that list.
- Vendor products get renamed. When a documented filename matches nothing,
  check whether the product still has the same name before assuming the
  download failed.
- Read the version out of the artifact rather than assuming it. Java and
  MongoDB requirements are keyed to the controller version, and that version
  is printed in the filename.
- Size a container for its *peak* demand, not its steady state. First-run
  initialization was the high-water mark, and steady-state usage sits well
  below it.
