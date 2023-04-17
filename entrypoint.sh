#!/bin/sh -l

python /src/main.py -c "$1" --t "$2"
BUILD_RESULT=$?
if [ $BUILD_RESULT -eq 0 ]; then
  echo ::set-output name=success::true
  exit 0
else
  echo ::set-output name=success::false
  exit 1
fi
