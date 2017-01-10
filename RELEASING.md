# Release process

## Resulting artifacts
Creating a new release creates the following artifacts:
- Container images:
  - `calico/node:$VERSION` and `calico/node:latest` 
  - `calico/ctl:$VERSION` and `calico/ctl:latest`
  - `quay.io/calico/node:$VERSION` and `quay.io/calico/node:latest`
  - `quay.io/calico/ctl:$VERSION` and `quay.io/calico/ctl:latest`
- Binaries (stored in the `dist` directory) :
  - `calicoctl`
  - `calicoctl-darwin-amd64`
  - `calicoctl-windows-amd64.exe`

## Preparing for a release
1. Make sure you are on the master branch and don't have any local uncommitted changes. e.g. Update the libcalico-go pin to the latest release in glide.yaml and run `glide up -v`, create PR, ensure test pass and merge.

2. Login using your dockerhub credentials (`docker longin` in your terminal). Make sure you have write access to calico orgs on Dockerhub and quay.io. 

3. Update the sub-component versions in the `Makefile` 
- `CONFD_VER := v0.10.0-scale`
- `BIRD_VER := v0.2.0`
- `GOBGPD_VER := v0.1.1`
- `FELIX_VER := 2.0.0`
- `LIBNETWORK_PLUGIN_VER := v1.0.0`
- `LIBCALICOGO_VER := v1.0.0`
- `LIBCALICO_VER := v0.19.0`- Currently, the startup.py script relies on the Python version of libcalico

3. Follow the steps from [Creating the release](https://github.com/projectcalico/calicoctl/blob/master/RELEASING.md#creating-the-release) section

## Creating the release
1. Choose a version e.g. `export VERSION=v1.0.0`
2. Create the release artifacts repositories `make release VERSION=$VERSION`. 
3. Follow the instructions to push the artifacts and git tag.
4. Create a release on Github, using the tag which was just pushed. 
5. Attach the following `calicoctl` binaries:
   - `calicoctl`
   - `calicoctl-darwin-amd64`
   - `calicoctl-windows-amd64.exe`
6. Add release notes for `calicoctl` and `calico/node`. Use `https://github.com/projectcalico/calicoctl/compare/<previous_release>...<new_release>` to find all the commit messages since the last release.
