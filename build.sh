#!/usr/bin/env bash

set -ex

cd jq
autoreconf -i
./configure CFLAGS=-fPIC --disable-maintainer-mode --with-oniguruma=builtin --disable-shared --enable-static --enable-all-static
make
