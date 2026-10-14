<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# Day-2 operations

## Backup and restore

Sources: [Backing up](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/Backup-and-restore/backing-up-sov-core.html) and
[Restoring your data](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/Backup-and-restore/restoring-your-data.html).

- **Where:** run backups from the UI, under **System configuration >
  Backup and restore**. They go to S3-compatible storage.
- **What is covered:** control-plane databases, IAM, compliance data, and
  observability data.
- **What is not covered:** tenant workload data and OpenShift itself.
  Recommend etcd backups and a tenant-data plan alongside.
- **When:** always take a backup before an upgrade.
- **Restores** overwrite current state. Confirm the restore point and the
  scope with the user before starting one.

## Observability

Source: [Observability overview](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/Observability/observability-overview.html).

The observability stack is built from:

- Loki for logs;
- Prometheus for metrics;
- Tempo for traces;
- the OpenTelemetry Collector;
- ClusterLogForwarder, for forwarding logs;
- Perses, for dashboards.

Audit logs can be routed to a SIEM; see "Audit log" in the documentation.

## Platform CLI (`sov-core-platform`)

Source: [Platform CLI](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/IBM-curated-Sovereign-Control-catalog/sc-platform-cli.html)
and [CLI and API overview](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/platform-cli-api-overview.html).

- **Install:** the CLI downloads automatically to the landing server.
- **Log in:** `sov-core-platform login --server <url> --token <token>`. The
  user supplies the token.
- **Config file:** `~/.sov-core/sov-core-platform/config.yaml`.
- **Command groups:** `status`, `whoami`, `system-owner`,
  `tenant-accounts`, `workspaces`, `services-ai-inference`, `ipam-dns`,
  `registry`, and others. Use `--help` on each group rather than
  guessing flags.
- **Confirmation:** read-only commands such as `status`, `whoami`, and
  list operations are safe. Commands that create, change, or delete
  tenants, workspaces, or services need confirmation.

Other CLIs:

- the Compliance center CLI (`sov-core`);
- the Vault CLI for the built-in Vault.

REST APIs are listed on the
[IBM API Hub](https://developer.ibm.com/apis/catalog/sovcore--ibm-sovereign-core-apis/Introduction).

## Certificates

Certificate rotation is documented under Installation > certificate
rotation. Track the expiry dates of the API and wildcard ingress
certificates, which must be valid for at least 90 days when installed.

## Related public material

[IBM/SovereignCore](https://github.com/IBM/SovereignCore) (Apache-2.0)
contains:

- alert runbooks, for Vault, IAM, Postgres, ArgoCD and pipelines, and more;
- GPU configuration examples;
- helper scripts.

Read a script before running it, and confirm with the user before running
anything that changes the cluster.
