#!/bin/sh
# Builds zipstock-theme.zip: the theme and the install notes.
set -e
cd "$(dirname "$0")"
rm -f zipstock-theme.zip
cp INSTALL.txt theme/ZIPSTOCK-README.txt

(cd theme && zip -qr -X ../zipstock-theme.zip .rockbox ZIPSTOCK-README.txt -x '*.DS_Store')
rm theme/ZIPSTOCK-README.txt
echo zipstock-theme.zip
