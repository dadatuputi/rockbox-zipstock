#!/bin/sh
# Builds zipstock-theme.zip: the theme, the install notes and the licence.
set -e
cd "$(dirname "$0")"
rm -f zipstock-theme.zip
cp INSTALL.txt theme/ZIPSTOCK-README.txt
cp LICENSE theme/ZIPSTOCK-LICENSE.txt

(cd theme && zip -qr -X ../zipstock-theme.zip .rockbox ZIPSTOCK-README.txt ZIPSTOCK-LICENSE.txt -x '*.DS_Store')
rm theme/ZIPSTOCK-README.txt theme/ZIPSTOCK-LICENSE.txt
echo zipstock-theme.zip
