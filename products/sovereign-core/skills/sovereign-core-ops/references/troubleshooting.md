<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# Troubleshooting

Sources:

- [Must-gather usage guide](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/Must-gather/must-gather-usage-guide.html)
- [Known issues and limitations](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/TS/known-issues-and-limitations.html)
- the troubleshooting table at the end of the
  [Prerequisite checklist](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/Planning/checklist-prerequisites.html)

## Gather evidence first: must-gather

Collecting diagnostics is read-only for the cluster. You need cluster-admin
access, and 500 MB–2 GB of free space for the bundle. Log in with
`oc login <cluster-url>` first.

```text
oc adm must-gather --image=icr.io/cpopen/sovereign-cloud-platform/sovcore-must-gather:<version> -- gather [OPTIONS]
```

| Goal | Options |
|---|---|
| Everything | *(none)* |
| Quick overview, no detailed logs | `-m overview` |
| Only failed resources | `-m failures` |
| Specific namespaces | `-n vault,vault-aas` |
| Sovereign Core namespaces only | `-p sovcore` |
| Full resources and logs for given namespaces | `--modes resources --namespaces vault,vault-aas,sovereign-ui` |

The output is `sovcore-must-gather-<timestamp>.tar.gz` under
`/must-gather/`. Review `collection.log` inside it for collection errors.
This bundle is what IBM Support needs.

## Installation failures

- **`validations.sh` fails (exit 1).** Fix the reported item, which is
  usually a prerequisite, and rerun. Common causes:
  - wrong OS version (`/etc/os-release` must show RHEL 10.1);
  - an inactive RHEL subscription;
  - firewall egress blocked to a registry;
  - DNS or certificate mismatches;
  - insufficient `/home` space.
- **Customer-provided OpenShift.** Check `SovereignCore/bootstrap-tracker`
  and rerun only the failed phase.
- **Logs.** An IBM Community walkthrough (not product documentation)
  reports installer logs under `~/logs/*.log` and
  `ocp-cluster/.openshift_install.log` on the landing zone. Confirm the
  paths on your system.

## Known issues to check (1.2.x)

The documentation lists known issues and workarounds, including:

- ArgoCD pipeline failures and webhook errors;
- IBM Verify Identity Access (IVIA) instability or stale state;
- an ODF StorageCluster stuck during creation;
- Tempo and Loki issues;
- NetObserv pods stuck in `ContainerCreating`.

Match the user's symptoms against that page for their exact version
before proposing changes.

## Ground rules for fixes

- Propose a fix only after evidence such as must-gather output, logs, or
  `oc get`/`oc describe` output points to a cause.
- Every `oc patch`/`delete`/`apply`, restart, or rerun of an install or
  upgrade step needs the user's confirmation.
- For production systems, prefer opening an IBM Support case with the
  must-gather bundle over trial-and-error changes.
