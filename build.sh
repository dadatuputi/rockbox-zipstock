#!/bin/sh
# Builds zipstock-theme.zip: the theme, the install notes and tag-books.py.
set -e
cd "$(dirname "$0")"
rm -f zipstock-theme.zip
cp INSTALL.txt theme/ZIPSTOCK-README.txt
cp tag-books.py theme/
(cd theme && zip -qr -X ../zipstock-theme.zip .rockbox ZIPSTOCK-README.txt tag-books.py -x '*.DS_Store')
rm theme/ZIPSTOCK-README.txt theme/tag-books.py
echo zipstock-theme.zip
