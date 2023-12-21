#!/usr/bin/env bash
#
# Run this script to setup Browser profile for the RPA
# You need resource credentials (e.g.: ChatGPT)
#

usage() {
  echo ""
  echo "Usage"
  echo " ./yoqu_configure.sh <config_file.json>"
  echo ""
  exit 1
}

[ $# -ne 1 ] && usage

config=$1
if [ ! -f "${config}" ];then
  echo "ERROR: Cannot open file '${config}'"
  exit 1
fi


#
# Chrome profiles folder
mkdir chrome_data 2>/dev/null
#
what="`jq -r '.type  + " (" + .desc + ")"' ${config}`"
url_login="`jq -r '.resource.url_login' ${config}` "
cmd="`jq -r '.resource.command | join(" ")' ${config}` ${url_login}"

echo "================================================================================"
echo "==> Configuration from file '${config}'":
echo "==> '${what}'"
echo "==> Cmd: ${cmd}"
echo "==> Launching Chrome, please login, then close the browser"
echo "================================================================================"
${cmd} >/dev/null 2>&1



