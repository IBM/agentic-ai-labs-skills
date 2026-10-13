<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# Sovereign Core prerequisites (1.2.x)

Source: [Prerequisite checklist](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/Planning/checklist-prerequisites.html)
and [Planning and setting up](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=planning-setting-up).
Re-check these against the documentation for the user's exact version.
Walk through them with the user one by one, and record anything that is
not yet met.

## Hardware

Landing zone (runs the installer and the local registry mirror):

- **OS:** RHEL 10.1. The installer exits on any other OS; check `/etc/os-release`.
- **CPU:** 4+ cores.
- **Memory:** 8 GB minimum, 16 GB recommended.
- **Disk:** at least 2.5 TB of fast local storage (NVMe), split as follows:
  - `/`: 500 GB.
  - `/home`: 2 TB on a **dedicated** NVMe volume, never shared with root.
    `/home` holds oc-mirror data, image caches, and the registry mirror.
  - Free space: the documentation asks for at least 2 TB free on `/home`
    plus 100 GB more, but elsewhere it says "2.5 TB". When in doubt, aim
    for the larger figure. Check with `df -h /home /`.
- **Network:** 2 NICs with management access.

Control plane:

- three bare-metal machines;
- each with 64+ cores (x86_64), 256 GB RAM, and 4 × 2 TiB PCIe Gen4+ NVMe.

Tenant worker plane:

- at least one bare-metal machine;
- with the same per-node specification as the control plane.

Every node:

- **Firmware:** BMC/Redfish, BIOS/UEFI, storage and network firmware all
  updated to the latest vendor-supported versions. Outdated firmware breaks
  discovery, provisioning, and power management.
- **Management:** a Redfish-compatible BMC.
- **Boot:** network boot capability.

## Networking

- **Networks:** four separate, configured networks: management
  (IPMI/IMM), compute, storage, and network.
- **Addressing:** static IPs only. DHCP is not supported for cluster nodes.
- **Time:** an NTP server, set in `template.env` and `vars.yaml` before
  installation.
- **Egress during installation:** allow these destinations on port 443.
  After setup, the cluster operates without the internet.
  - Red Hat: `registry.redhat.io`, `access.redhat.com`,
    `registry.access.redhat.com`, `cdn.redhat.com`, `sso.redhat.com`
  - Quay: `quay.io` and `cdn.quay.io`, `cdn01`–`cdn06.quay.io`
  - IBM and OpenShift: `icr.io`, `cp.icr.io`, `mirror.openshift.com`
  - Ansible and Python: `pypi.org`, `files.pythonhosted.org`,
    `galaxy.ansible.com`, `cloud.redhat.com`
  - Utilities: `github.com`, `release-assets.githubusercontent.com`,
    `get.helm.sh`, `amazonaws.com`
- **Inbound ports to the landing zone:**
  - `22` (SSH);
  - `8443` (control plane access);
  - `8000` (OpenShift fetches the installation image from the landing zone).

## Supporting services

- **Corporate services:** SMTP, DNS, and an identity provider (LDAP/AD).
- **Storage:** a storage server for block and object storage. ODF is
  recommended. Ceph is **not** supported for production.
- **Backups:** S3-compatible object storage, used by the backup feature.

## Keys, secrets, and certificates

- **Red Hat pull secret** from console.redhat.com, covering
  cloud.openshift.com, registry.connect.redhat.com, quay.io, and
  registry.redhat.io.
- **Red Hat Customer Portal account** with an active subscription, and
  access to OpenShift Container Platform 4.20 and the Red Hat operators.
- **IBM entitlement key** for the IBM Container Registry. See "Getting your
  entitlement API key" in the docs.
- **SSH key** for node access after deployment.
- **API certificate:** key and full chain for
  `api.<cluster-name>.<base-domain>`.
- **Wildcard ingress certificate:** key and full chain for
  `*.apps.<cluster-name>.<base-domain>`.

All TLS certificates must remain valid for at least 90 days at install time.

## Installing user

- **Not root.** The installing user must not be root, and needs passwordless
  sudo.
- **`make`:** install it with `sudo yum install make`.
