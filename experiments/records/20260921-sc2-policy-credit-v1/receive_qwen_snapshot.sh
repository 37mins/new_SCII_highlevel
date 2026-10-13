#!/usr/bin/env bash
# Run once through the configured node197 SSH alias; stdin is the approved tar.
set -euo pipefail
staging=/var/jfsCache/sc2-qwen-instruct2507-cdbee75-20260921-r1-relay2-staging
published=/var/jfsCache/sc2-qwen-instruct2507-cdbee75-20260921-r1
test ! -e "${published}"
test -f "${staging}/manifest.sha256"
test ! -e "${staging}/model"
mkdir "${staging}/model"
trap 'status=$?; if (( status != 0 )); then printf "%s\n" "${status}" > "${staging}/FAILED.exit"; fi' EXIT
timeout 18000s tar -C "${staging}/model" -xf -
(cd "${staging}/model" && sha256sum -c ../manifest.sha256) > "${staging}/verification.log"
test "$(wc -l < "${staging}/verification.log")" -eq 12
cp "${staging}/verification.log" "${staging}/VERIFIED.sha256"
sync -f "${staging}/VERIFIED.sha256"
mv "${staging}" "${published}"
trap - EXIT
