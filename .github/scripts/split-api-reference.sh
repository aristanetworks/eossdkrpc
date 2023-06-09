#!/bin/sh

[ "$#" -eq 1 ] || exit 1

DIR=$1

# Splits files between each `--- proto_file_name.proto` marker.
csplit "$DIR/api-reference.md" \
    --quiet \
    --prefix "$DIR/proto-" \
    --elide-empty-files '/^--- [^.]*\.proto/' '{*}'

# TLDR: Rename generated files to the correct protofile names
#
# Each generated file is named `proto-xx` with `xx` being a number like `01`.
# Their first line is of form `--- proto_file_name.proto`.
# This loop removes this line and renames files to `proto_file_name.md`.
for TMP in $(ls "$DIR"/proto-*); do
    FILENAME=$(head -1 "$TMP" | sed 's/--- \([^\.]*\)\.proto/\1/')
    tail -n +2 "$TMP" > "$DIR"/"$FILENAME".md
    rm "$TMP"
done

rm "$DIR/api-reference.md"
