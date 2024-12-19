#!/bin/bash

SCRIPTDIR=$(dirname $0)
OUTDIR=$(realpath $SCRIPTDIR/../output)
BENCHMARKDIR=$(realpath $SCRIPTDIR/../benchmarks)

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <iterN>"
    exit
fi

if ls $OUTDIR/B1-noarg-* 1> /dev/null 2>&1; then
    echo "$OUTDIR/B1-noarg-* exists, please remove it."
    exit 1
fi

if ls $OUTDIR/result-B1-compare 1> /dev/null 2>&1; then
    echo "$OUTDIR/result-B1-compare exists, please remove it."
    exit 1
fi

mkdir -p $OUTDIR/result-B1-compare

# Run smartian, sFuzz, and mythril.
for i in $(seq $1); do
    python3 $SCRIPTDIR/run_experiment.py B1-noarg smartian 120
    python3 $SCRIPTDIR/run_experiment.py B1-noarg sFuzz 120
    python3 $SCRIPTDIR/run_experiment.py B1-noarg mythril 120
    python3 $SCRIPTDIR/run_experiment.py B1-noarg ityfuzz 120
done
mkdir -p $OUTDIR/result-B1-compare/smartian
mv $OUTDIR/B1-noarg-smartian-* $OUTDIR/result-B1-compare/smartian/
mkdir -p $OUTDIR/result-B1-compare/sFuzz
mv $OUTDIR/B1-noarg-sFuzz-* $OUTDIR/result-B1-compare/sFuzz/
mkdir -p $OUTDIR/result-B1-compare/mythril
mv $OUTDIR/B1-noarg-mythril-* $OUTDIR/result-B1-compare/mythril/
mkdir -p $OUTDIR/result-B1-compare/ityfuzz
mv $OUTDIR/B1-noarg-ityfuzz-* $OUTDIR/result-B1-compare/ityfuzz/

# python3 $SCRIPTDIR/convert_to_replayable.py B1 $BENCHMARKDIR $OUTDIR/result-B1-compare/smartian/ smartian
# python3 $SCRIPTDIR/convert_to_replayable.py B1 $BENCHMARKDIR $OUTDIR/result-B1-compare/mythril/ mythril
# python3 $SCRIPTDIR/convert_to_replayable.py B1 $BENCHMARKDIR $OUTDIR/result-B1-compare/sFuzz/ sFuzz
