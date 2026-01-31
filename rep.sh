#!/bin/bash

find . -type f -exec sh -c '
  for file; do
    if file "$file" | grep -q text; then
      sed -i "" "s/termeval_ab/termeval_ab/g" "$file"
    fi
  done
' sh {} +
