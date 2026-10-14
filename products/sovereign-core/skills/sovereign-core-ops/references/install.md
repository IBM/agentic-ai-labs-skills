<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus) -->

# Installing Sovereign Core (1.2.1)

Source: [Installing the latest version](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/Installation/installing_sovereign_core_121.html)
and [Validation checks](https://www.ibm.com/docs/en/sovereign-core/1.2.0?topic=SSCYBM3_1.2.0/Installation/validation-checks.html).

## Deployment models

- **Red Hat Enclave-based.** IBM supplies and manages the full Enclave
  infrastructure on bare metal.
- **Customer-provided Red Hat OpenShift.** `bootstrap.sh` first runs an
  *Enclave replacement* phase:
  1. mirror initial images;
  2. configure the maximum number of pods;
  3. install storage;
  4. install Quay;
  5. mirror the Red Hat operator images;
  6. install the Red Hat operators;
  7. install Clair.

  Progress is tracked in `SovereignCore/bootstrap-tracker`. If a phase
  fails, rerun only that phase, by number or name. Check the phase names
  against the installed `bootstrap.sh` first; the docs give them as an
  example only.

## Sequence

1. **Download the installer.**
   `oras pull icr.io/cpopen/sovereign-cloud-platform/sovcore-install:v1.2.1`
   downloads `SovereignCore-v1.2.1.tar.gz`. Extract it with `tar -xzvf`.
2. **Run the preinstallation tool.**
   - Prepare a `./data` directory, owned by `1001:0` and mode `775`.
   - Start the tool with
     `sudo podman run -d --replace --name config-file-generator -p 3003:3003 -v <dir>/data:/opt/app-root/src/data:Z icr.io/cpopen/sovereign-cloud-platform/install-ui:v1.2.1`.
   - Complete the Infrastructure, Control plane, and Tenant worker planes
     forms, then select **Finish**.
   - The tool writes `global.yaml`, `odf.yaml`, `certificates.yaml`, and
     `template.env`. These can also be edited by hand.
3. **Set the DNS record.** In `template.env`, set
   `GORI_CUSTOM_DNS_RECORDS=mirror.<baseDomain>:<landing-zone-ip>`.
4. **Run the installer** (confirm first). `tmux new -s scjob`, then
   `./bootstrap.sh`. It runs these in order:
   1. `validations.sh`;
   2. install-type detection, from `install-env.sh`;
   3. the Enclave replacement phase, for the customer-provided OpenShift
      model only;
   4. `start.sh`.

   When it finishes, it prints `Done...` with a timestamp. Expect several
   hours.
5. **Post-installation steps.** Confirm each one that changes something.
   1. Log in: `oc login --server=https://api.<cluster>.<domain>:6443` as
      `kubeadmin`. The password is in
      `${HOME}/ocp-cluster/auth/kubeadmin-password`; the user reads it
      themselves.
   2. Set the landing zone's name server to the embedded DNS virtual IP
      (`GORI_DNS_VIP`). Use `nmcli`, applying it to every active
      connection that has IP configuration; skip bond member ports. The
      documentation gives the exact loop.
   3. Configure block and object storage for each tenant, following
      capacity planning.
   4. Optional plugins:
      - `make deploy-plugin PLUGIN=openshift-ai`
      - `make deploy-plugin PLUGIN=nvidia-gpu`
      - `make deploy-plugin PLUGIN=clair-import` (the vulnerability database)

## Validation (`validations.sh`)

- **Run order:** it runs automatically as the first step of `bootstrap.sh`.
  Exit code 0 means pass and 1 means fail.
- **Tools:** it checks for, or installs, these tools:
  - `oc` 4.20.21
  - `helm` 3.19.4
  - `yq` and `jq`
  - `oras` 1.3.0
  - `tkn` 0.43.0
- **Configuration:** it also checks the identity, SMTP, DNS, storage,
  registry, and OADP/Velero settings.
- **When it fails:** fix the reported item and rerun. Don't bypass it.

## After installation

| What | URL |
|---|---|
| OpenShift console | `https://console-openshift-console.apps.<cluster>.<domain>` |
| Sovereign Core home (system users) | `https://mspui.apps.<cluster>.<domain>` |
| Identity provider dashboard | `https://identity.apps.<cluster>.<domain>` |

These configuration files live on the landing zone only:

- `values.yaml` holds constant values.
- `values-dynamic.yaml` is generated from the cluster.
- `secrets.yaml` holds credentials. Treat it as a secret.

Known: an `ibm-solis-embedded-keycloak` pod in `CrashLoopBackOff` in the
`concert-hub` namespace can be ignored. The documentation says it does not
affect the Compliance center.
