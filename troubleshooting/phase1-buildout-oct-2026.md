# Phase 1 Build-Out — Troubleshooting Log

**Dates:** 2026-10-22 → 2026-10-28
**Scope:** OPNsense firewall driver installation, Proxmox VE installation,
and network integration of the completed rack.

Three distinct problems came up across this build. None of them were caused
by the thing I was actually trying to configure — the pattern across all
three was that the failure sat one or two layers below where I was looking.

---

## Incident 1 — OPNsense: Realtek NIC drivers

**Date:** 2026-10-22

### Goal

The BOSGAME E5 Plus uses Realtek 2.5G NICs. Install the `os-realtek-re`
vendor driver package from a USB drive so the interfaces enumerate and can
be assigned as WAN and LAN.

The constraint: no network interfaces were assigned yet, so the box had no
internet access and the package had to come in over USB.

### Issues encountered

**1. Comma in the device path**

Attempted to mount `/dev/da0,pass1`. The comma was not part of a path —
`camcontrol` lists two device nodes for the same physical drive, the block
device (`da0`) and the passthrough device (`pass1`), separated by a comma.
Only `da0` is mountable.

*Fix:* used `/dev/da0` as the base device.

**2. Partition numbering starts at 1**

Attempted `/dev/da0p0`. FreeBSD numbers partitions from 1, so `p0` never
exists on any disk.

*Fix:* used `p1`.

**3. `mount: Invalid argument` — filesystem, not path**

`mount -t msdosfs /dev/da0p1 /mnt/usb` returned `Invalid argument`. This is
a different class of error from "No such file or directory" — the device
node existed and was readable, but the filesystem on it was not msdosfs.

`gpart show da0` confirmed a GPT scheme with a single `ms-basic-data`
partition. A 128GB drive formatted by Windows defaults to exFAT, and
**FreeBSD's base system has no exFAT support.** The in-kernel NTFS driver
was removed years ago as well, and the replacement (`fusefs-ntfs`) is itself
a package — which cannot be installed without network access. Chicken and
egg.

*Fix:* reformat the drive as FAT32.

**4. The 32GB FAT32 limit does not exist**

Windows' format dialog refuses to create a FAT32 volume larger than 32GB.
This is a limitation of the dialog, not of FAT32 — the filesystem supports
volumes up to 2TB.

*Fix:* used Rufus with the **"Large FAT32"** file system option, Non-bootable,
MBR partition scheme. Alternatives that also work: shrink the partition to
under 32GB in Disk Management, or use Ridgecrop's `guiformat`.

**5. Missing space in the mount command**

`mount -t msdosfs /dev/da0s1/mnt/usb` printed the `mount` usage text rather
than an error. The missing space meant the shell passed one argument instead
of two, so `mount` rejected the invocation before ever touching the device.

The usage output is the tell — a genuine mount failure names the device.

*Fix:* `mount -t msdosfs /dev/da0s1 /mnt/usb`

Note the device node also changed from `da0p1` to `da0s1` after the
reformat, because Rufus wrote an MBR scheme rather than GPT. FreeBSD uses
`s` (slice) for MBR partitions and `p` for GPT partitions.

**6. Package install order**

The driver package and its components had to be installed in a specific
order for `pkg add` to resolve them locally without network access.

### Outcome

`os-realtek-re` installed cleanly — plugin registered and firmware settings
written. Rebooted rather than using `kldload`, since the OPNsense plugin
wires the vendor driver into the boot loader so it loads in place of the
base `re` driver. Interfaces enumerated on reboot and were assigned.

### Takeaways

- `Invalid argument` from `mount` means the filesystem is wrong, not the
  path. `No such file or directory` means the path is wrong. They are
  different failures and point in different directions.
- FreeBSD device naming encodes the partition scheme: `da0p1` = GPT,
  `da0s1` = MBR. The node name itself tells you how the disk was written.
- When a command prints its own usage text, the problem is in the
  invocation, not the target.
- Check what the chip actually is before chasing a driver package. The base
  `re` driver handles most 1G Realtek parts (8168/8111) fine; the vendor
  package mainly matters for the 2.5G chips (8125/8126).

---

## Incident 2 — Proxmox VE: installation media and BIOS

**Date:** 2026-10-25
**Host:** HP EliteDesk 800 G4 Mini

### Goal

Install Proxmox VE 9.2 from USB onto the EliteDesk.

### Issues encountered

**1. The ISO was copied, not written**

The USB drive contained `proxmox-ve_9.2-1.iso` as a visible 1.6GB file
sitting on a FAT32 volume, alongside a leftover `autorun.inf` from the
previous job. No firmware will boot that — there is no bootloader anywhere
on the disk. The ISO's contents have to *become* the drive's structure, not
sit inside it as a file.

*Fix:* rewrote the drive with Rufus. Proxmox ships a **hybrid ISO**, which
must be written in **DD Image mode** — Rufus prompts for ISO vs DD mode on
START and defaults to ISO mode, which produces exactly the non-bootable
result above.

Moved the ISO off the target drive first; Rufus cannot read its source from
the drive it is overwriting.

**2. Windows reports the correct result as a failure**

After a successful DD write, Windows prompted that the drive "needs
formatting" and showed two unreadable partitions. This is correct behavior
— the drive now holds a Linux filesystem plus an EFI system partition,
neither of which Windows can read. Formatting at that prompt destroys the
installer.

**3. F9 and F10 not registering**

Neither the one-time boot menu (F9) nor BIOS setup (F10) would open.

Two separate causes, both in the BIOS:
- **Fast Boot** was enabled, which skips most of POST — including the window
  where the firmware listens for keystrokes, and before USB is initialized.
- **Startup Delay** was set to `0`, leaving no margin at all for a USB
  keyboard to initialize and send a keypress.

Windows 11 **Fast Startup** compounds this separately: with it enabled,
"shut down" is a hybrid sleep rather than a cold boot, so POST barely runs.

*Workaround while locked out:* Settings → System → Recovery → Advanced
startup → Troubleshoot → Advanced options → **UEFI Firmware Settings**.
This reaches the BIOS without any key timing at all.

*Fix:* disabled BIOS Fast Boot, set Startup Delay to 5 seconds, and disabled
Windows Fast Startup.

**4. USB drive absent from the boot order**

Even with a correctly written stick and USB Storage Boot enabled, the drive
did not appear in the UEFI boot order — only `SATA0: Windows Boot Manager`
and the two network boot entries. Reordering cannot help when the device is
not enumerated at all.

*Fix:* disabling Fast Boot caused the firmware to enumerate USB during POST,
and `USB:` appeared in the boot order on the next entry into setup.

**5. The keyboard was the actual root cause**

The installer booted to the GRUB menu and then accepted no input — arrows,
Enter, and Esc all did nothing.

This was the same underlying problem as the F9/F10 failures: **the keyboard
was not functional before an OS loaded.** Wireless keyboards do not work
pre-OS, and keyboards behind hubs or KVMs frequently do not pass keystrokes
during POST.

*Fix:* swapped to a different keyboard. Both symptoms resolved immediately.

**6. Timezone defaulted incorrectly**

The installer summary showed `America/Adak` (Aleutian Islands, UTC-9) rather
than the Eastern timezone. Caught at the confirmation screen.

This is not cosmetic — every log timestamp, cron schedule, backup window,
and certificate validity check on the host runs off that clock.

*Fix:* corrected to `America/New_York` before installing. Verified after
first boot with `timedatectl`.

### Outcome

Proxmox VE 9.2 installed to `/dev/sda` (500GB SATA SSD, ~475GB usable) with
ext4. First boot reached the login banner and the management URL.

### Takeaways

- An ISO file visible in Explorer on the USB drive means the write did not
  happen. A correctly written installer is *not* readable by Windows.
- Proxmox's hybrid ISO requires DD mode in Rufus. ISO mode silently produces
  a non-bootable drive.
- If a device is missing from the boot order entirely, the problem is
  enumeration, not ordering — look at Fast Boot before touching Secure Boot.
- When input fails *before* an OS loads, suspect the input device. One bad
  keyboard produced two symptoms that looked like three different firmware
  problems.
- Read the installer summary screen. The timezone default was wrong and
  would have quietly corrupted every timestamp on the host.

---

## Incident 3 — Subnet collision and network re-addressing

**Date:** 2026-10-27

### Goal

Integrate the assembled rack: Verizon 5G router → OPNsense → switch →
Proxmox, both workstations, and the AP.

### Issues encountered

**1. Subnet collision with the upstream router**

OPNsense's LAN defaults to `192.168.1.1/24`. The Verizon 5G router upstream
also serves `192.168.1.0/24`. Two routers claiming the same address on a
double-NAT path produces confusing and intermittent symptoms.

Caught before power-on by checking the upstream router's subnet with
`ipconfig`. Worth doing *before* wiring anything, not after.

*Fix:* migrated the OPNsense LAN to `192.168.10.0/24`.

**2. Link up, no DHCP — wrong physical port**

The workstation pulled a `169.254.x.x` APIPA address: link established
(the adapter was not reporting "Media disconnected"), but nothing answering
DHCP.

Cause: the switch uplink was plugged into the OPNsense **WAN** port. The
link negotiates normally, but WAN does not serve DHCP — so this looks like a
DHCP service failure rather than a cabling error.

There is no reliable mapping between the logical interface name (`re0`) and
which physical jack it is on a given chassis.

*Fix:* moved the cable to the other port. **On this box, LAN (`re0`) is the
rear-left port viewed from the front.** This is now labeled on the chassis
and recorded in `network/current-state.md`.

**3. Order of operations during re-addressing**

Re-addressing the firewall first would have stranded the Proxmox host —
sitting at `192.168.1.47` on a subnet that no longer existed, reachable only
with a monitor and keyboard.

*Fix:* changed Proxmox to `192.168.10.47/24` **first**, while it was still
reachable, then moved the OPNsense LAN.

**4. Documentation drift — ISC DHCPv4 vs Dnsmasq**

Most OPNsense guides reference *Services → ISC DHCPv4*. This build is on
OPNsense 26.7, where the LAN DHCP server is **Dnsmasq DNS & DHCP**. The ISC
path does not exist.

The interface address must be changed *before* the DHCP range, or the range
is rejected for not matching the interface subnet.

*Fix:* Interfaces → LAN → `192.168.10.1/24`, then Services → Dnsmasq DNS &
DHCP → DHCP ranges → `192.168.10.100` – `192.168.10.199`.

**5. Proxmox network changes require a separate Apply**

After changing `vmbr0`, Proxmox was unreachable at both the old and new
addresses. Saving a network change in the Proxmox web UI writes it to a
pending file; a separate **Apply Configuration** action commits it.

*Fix:* a reboot applied the pending configuration. The `Apply Configuration`
button does the same without the downtime.

**6. Subnet math — where the boundary falls**

Worth recording because the reasoning error is a common one. `192.168.100.x`
and `192.168.1.1` are *not* on the same network under a /24, even though 100
is below 128.

The 128 boundary only matters when the prefix splits **inside** an octet:

| Prefix | Mask | Boundary falls | `192.168.1.1` and `192.168.100.10` |
|---|---|---|---|
| /24 | 255.255.255.0 | after 3rd octet | different networks |
| /17 | 255.255.128.0 | inside 3rd octet | same network |
| /16 | 255.255.0.0 | after 2nd octet | same network |

Under /24 the first three octets are entirely network, so the third octet
must match exactly — there is no block math in it. Under /17 the boundary
lands inside the third octet and splits it at 128, and both addresses fall in
the lower half.

Also caught during this step: `192.168.100.465` was entered as an address.
Octets max at 255.

### Outcome

Workstation pulled `192.168.10.107/24`, gateway `192.168.10.1`, with the
`internal` DNS suffix confirming OPNsense as the responding DHCP server
rather than the upstream router. Both web UIs reachable on their new
addresses.

### Takeaways

- Check the upstream router's subnet *before* wiring a second router in.
  Five minutes with `ipconfig` prevents an hour of re-addressing.
- APIPA (`169.254.x.x`) with a live link means DHCP is not answering —
  check which physical port the cable is in before suspecting the service.
- When re-addressing a chain of devices, work from the far end inward. Move
  the host that will be stranded first, while it is still reachable.
- Verify the software version against the guide. OPNsense moved from ISC
  DHCPv4 to Dnsmasq; following a stale guide sends you to a menu that is not
  there.
- Label the physical ports as soon as you identify them. Logical interface
  names do not map predictably to jacks.

---

## Cross-cutting notes

Three days of troubleshooting, and the actual causes were: a comma, a
filesystem, a missing space, a write mode, a keyboard, and a cable in the
wrong jack. Not one of them was the driver, the hypervisor, or the firewall.

Patterns worth carrying forward:

- **Read the exact error text.** `Invalid argument` vs `No such file or
  directory` vs a usage dump are three different diagnoses.
- **Change one thing at a time.** Secure Boot was never the problem, but it
  was the obvious suspect and would have been changed for no reason.
- **Suspect the layer below.** Driver problem → filesystem problem. BIOS
  problem → keyboard problem. DHCP problem → cabling problem.
- **Get console access early.** Several of these would have been five-minute
  fixes with a monitor attached rather than hour-long inferences.
