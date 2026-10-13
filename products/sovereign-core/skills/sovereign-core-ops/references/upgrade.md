<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# Upgrading Sovereign Core (to 1.2.1)

Sources:

- [Upgrading the software](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/upgrade/softwareupgrade.html)
- [Step 1: Upgrading Red Hat OpenShift](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/upgrade/upgrading-red-hat-121.html)
- [Step 2: Upgrading to the latest version](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/upgrade/upgrade121.html)

An upgrade has **two steps, and both are required**. Run them from the
landing zone. Only system owners can run Step 2. Before starting, check
the "Upgrading AI inference service" page to avoid disrupting inference.

## Before you start

1. **Back up.** Take a control-plane backup; see
   [day2-operations.md](day2-operations.md).
2. **Save the configuration files** from the previous version:
   `global.yaml`, `certificates.yaml`, `cloud_infra.yaml`, `odf.yaml`,
   and `template.env`. Merge them into the new version's folder.

## Step 1: OpenShift and operators

Confirm each command that changes something.

1. **Download and extract the new release.**
   `oras pull icr.io/cpopen/sovereign-cloud-platform/sovcore-install:v1.2.1`,
   then `tar -xzvf SovereignCore-v1.2.1.tar.gz -C ${HOME}`.
2. **Point `oc` at the cluster.**
   `export KUBECONFIG=${HOME}/ocp-cluster/auth/kubeconfig`.
3. **Mirror the new content:** `./sync.sh`. If it hangs for more than an
   hour, apply the OADP subscription patch from the documentation.
4. **Apply configuration updates and migration:** `./upgrade.sh`.
5. **Upgrade the management cluster:**
   `enclave reconcile mgmt-cluster-version --use-defaults`.
6. **Upgrade the operators:**
   `enclave reconcile operator-versions --use-defaults`.
7. **Verify:**
   - `oc get catalogsource -n openshift-marketplace` lists the
     `cs-redhat-operator-index-v4-20` and `…-odf-v4-20` sources;
   - `oc get clusterversion` shows the target version, with Available
     True;
   - `oc get nodes` shows every node Ready.

   Don't start Step 2 until all three checks pass.

## Step 2: Platform and services

1. **Reset the install tracker first.** This is a silent-failure trap. If
   you extracted the new package into a directory used by an earlier
   deployment, `${HOME}/SovereignCore/partner-install/install-tracker.yaml`
   may still say `STEP: "complete"`. In that case image mirroring is
   **silently skipped**. Change it to `STEP: "1"`.
2. **Mirror the images:**
   `export MIRROR_ONLY=true; ./bootstrap.sh --step partner-overlay`.
3. **Install the pipelines.** Install the backup-restore pipelines, then
   the Sovereign Core upgrade pipelines, from the local Quay registry using
   the documented `helm upgrade --install … --namespace openshift-pipelines`
   commands. Copy the chart references and versions exactly from the
   documentation for your version.

   The documented commands pass `--insecure-skip-tls-verify` to the local
   registry. Point this out to the user, and use the registry's CA instead
   if their environment allows it.
4. **Start the upgrade.** Create the upgrade `PipelineRun` from the
   documented template, filling in:
   - the registry;
   - the apps domain;
   - the cluster ID;
   - the target OpenShift version.

   Then `oc create -f` it, and follow its progress with `tkn`.

From 1.2.0 onward, upgrades can also be scheduled from the Sovereign Core
UI.
