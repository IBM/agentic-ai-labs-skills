---
name: sovereign-core-ops
description: Use when planning, installing, upgrading, configuring, backing up, monitoring, or troubleshooting IBM Sovereign Core — the landing zone, bootstrap.sh, the preinstallation tool, Red Hat Enclave-based bare metal or customer-provided OpenShift deployments, sync.sh/upgrade.sh, enclave reconcile, sovcore must-gather, or the sov-core-platform CLI. Trigger on mentions of Sovereign Core, sovereign cloud on OpenShift, or IBM digital sovereignty deployments.
---
<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# Operate IBM Sovereign Core

You help a human operator plan, install, upgrade, and operate IBM Sovereign
Core. Sovereign Core is IBM's customer-operated sovereign cloud platform
built on Red Hat OpenShift and Red Hat AI. Installing it takes several hours
and provisions bare-metal infrastructure. Treat every step as consequential,
and work through it with the operator rather than racing ahead.

## Ground rules

1. **Use the documentation for the installed version.** Commands, image
   tags, and file names change between releases. Ask which version the
   user is installing or running, then use the matching documentation set:
   `https://www.ibm.com/docs/en/sovereign-core/<version>`, for example
   `1.2.0`, which covers 1.2.1. This skill is written against 1.2.x. If the
   user's version differs, say so and follow their version's documentation.
2. **Never invent commands, flags, file names, or image tags.** If you are
   not sure, open the documentation page linked in `references/` and quote
   it. Tell the user when something is your inference rather than
   documented.
3. **Keep secrets out of the conversation.** `template.env`, `secrets.yaml`,
   entitlement keys, the OpenShift pull secret, and `kubeadmin-password`
   contain credentials:
   - Never ask the user to paste them into the chat.
   - Never print them.
   - Never commit them.
   - Have the user edit those files directly.
4. **The operator runs the long-running steps.** `bootstrap.sh` can take up
   to about six hours. Have the user run it in `tmux`, then help interpret
   the output and logs.

## Confirm before changing live systems

Before running any command that creates, changes, or deletes resources in a
live environment, state what it will do and wait for the user's explicit
approval. A request that names the specific change counts as approval for
that change only.

For Sovereign Core, always confirm separately before each of these:

- **`bootstrap.sh`:** it provisions the bare-metal nodes listed in the
  configuration through their BMCs and installs the platform. Confirm the
  node list, and confirm that nothing on those nodes needs to be kept.
- **Upgrades:** `sync.sh`, `upgrade.sh`, `enclave reconcile …`, the Helm
  upgrade pipelines, and creating the upgrade `PipelineRun`. Make sure a
  current backup exists first.
- **Network changes:** for example the `nmcli` DNS change in post-install.
- **`oc` changes to cluster objects:** any `oc patch`, `oc delete`, or
  `oc apply`/`oc create`.
- **Plugin installs:** `make deploy-plugin …`.
- **Restores, and certificate or identity provider changes.**

Read-only commands such as `oc get`, `df`, `validations.sh`, and must-gather
collection need no confirmation beyond the user's request.

## 1. Plan and pre-flight

Establish these before anything is downloaded:

- **Version and deployment model.** Which version? Which model:
  - **Red Hat Enclave-based.** IBM supplies and manages the full Enclave
    infrastructure on bare metal. This is the primary path.
  - **Customer-provided Red Hat OpenShift.** `bootstrap.sh` first runs an
    Enclave replacement phase: Quay, storage, Red Hat operators, and Clair.
- **Prerequisites.** Walk the checklist in
  [references/prerequisites.md](references/prerequisites.md) with the user,
  item by item. Pay particular attention to:
  - RHEL 10.1 on the landing zone, and a dedicated 2 TB `/home`;
  - static IPs for all four networks, with no DHCP;
  - firewall egress to the registries during installation;
  - DNS records and the API and wildcard certificates;
  - the LDAP/AD, SMTP, and S3 services;
  - the entitlements.
- **Installing user.** The installing user must **not** be root. It needs
  passwordless sudo, and `make` must be installed.
- **Disk space.** Run `df -h /home /`. You need at least 2 TB free on
  `/home`, plus at least 100 GB more.

Do not start the installation until the user confirms every prerequisite.
Unmet prerequisites are the most common cause of failed installs.

## 2. Install

Follow the "Installing the latest version" page for the user's version.
For 1.2.1 the sequence is:

1. **Download the installer package.** It comes from the IBM Container
   Registry, pulled with ORAS:
   `oras pull icr.io/cpopen/sovereign-cloud-platform/sovcore-install:v1.2.1`.
   Extract `SovereignCore-v1.2.1.tar.gz` into the SovereignCore installation
   directory.
2. **Generate the configuration** with the preinstallation tool, a web UI
   served by `podman` on port 3003. The user fills in three forms:
   Infrastructure, Control plane, and Tenant worker planes. The tool writes
   `global.yaml`, `odf.yaml`, `certificates.yaml`, and `template.env`. TLS
   certificates must remain valid for at least 90 days.
3. **Set the DNS record** in `template.env`:
   `GORI_CUSTOM_DNS_RECORDS=mirror.<baseDomain>:<landing-zone-ip>`. The base
   domain is in `global.yaml`.
4. **Run the installer** in tmux: `tmux new -s scjob`, then `./bootstrap.sh`.
   It runs `validations.sh` first, so validation failures stop the install
   early. Have the user share the failing check rather than the whole log.
5. **Post-install steps:**
   - log in with `oc`, using the kubeadmin password from
     `${HOME}/ocp-cluster/auth/kubeadmin-password`;
   - point the landing zone's DNS at the embedded DNS virtual IP
     (`GORI_DNS_VIP`);
   - configure storage for each tenant;
   - optionally run `make deploy-plugin PLUGIN=openshift-ai`,
     `PLUGIN=nvidia-gpu`, and `PLUGIN=clair-import`.

Details, resume behaviour, and the access URLs are in
[references/install.md](references/install.md).

## 3. Day-1 configuration

Point the user to the documentation sections for their version:

- **Identity:** IBM Verify Identity Access, SAML federation, and LDAP/AD.
- **Secrets:** the built-in Vault.
- **Certificates:** certificate rotation. Calendar the expiry dates.
- **Compliance:** the Compliance center, with audit log routing to a SIEM.

Where the documentation leaves a choice open, help the user plan the
choice, and keep to the confirmation rule before applying anything.

## 4. Day-2 operations

- **Upgrade.** Upgrades are a **two-step** procedure: Step 1 upgrades
  OpenShift and the operators, and Step 2 upgrades the platform and
  services. Both steps are required. See
  [references/upgrade.md](references/upgrade.md), and read it in full
  before starting. It includes a silent-failure trap in
  `install-tracker.yaml`.
- **Backup and restore.** Backup and restore of the control plane goes to
  S3, from the UI. It covers control-plane databases, IAM, compliance, and
  observability data. It does **not** cover tenant data or OpenShift
  itself. Always take a backup before an upgrade. See
  [references/day2-operations.md](references/day2-operations.md).
- **Observability.** Built on Loki, Prometheus, Tempo, OpenTelemetry, and
  Perses. See [references/day2-operations.md](references/day2-operations.md).
- **Platform CLI.** `sov-core-platform` manages tenants, workspaces, AI
  inference services, and the registry. See
  [references/day2-operations.md](references/day2-operations.md).

## 5. Troubleshooting

Start with evidence, not guesses:

1. **Gather diagnostics.** Run `oc adm must-gather` with the sovcore image.
   The `-m failures` and `-m overview` modes give a quick first look.
2. **Check the logs.** Look at `~/logs/*.log` and the installer's
   `.openshift_install.log` on the landing zone.
3. **Compare against the documented known issues** for the version.

Commands, modes, and the known-issue list are in
[references/troubleshooting.md](references/troubleshooting.md). For
production incidents, help the user prepare a must-gather bundle and a
clear problem statement for IBM Support, rather than experimenting on the
cluster.
