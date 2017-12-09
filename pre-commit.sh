#!/bin/sh

to_commit=$(git diff --cached --name-only --diff-filter=ACM)

for file in ${to_commit}; do
  MD5=$(egrep -v "^MD5: " ${file} | md5 -q)
  echo "Calculating MD5 for ${file}: ${MD5}"
  sed -i '.tmp' 's/^\(MD5: \).*/\1'${MD5}'/g' ${file} && \
  rm ${file}.tmp
done

