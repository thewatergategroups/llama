#! /bin/bash
for D in /secrets/*/*; do
set -a
C=(${D//// })
export "${C[2]}"="$(cat $D)"
set +a
done 
exec "$@"