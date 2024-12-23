#!/bin/bash


# Arg1 : Time limit
# Arg2 : Source file
# Arg3 : Bytecode file
# Arg4 : ABI file
# Arg5 : Main contract name
# Arg6 : Optional argument to pass

WORKDIR=/home/test/ityfuzz-workspace

# Set up workdir
mkdir -p $WORKDIR
mkdir -p $WORKDIR/bench
mkdir -p $WORKDIR/output


# Copy source file and bytecode file into WORKDIR
cp $3 $WORKDIR/bench/
cp $4 $WORKDIR/bench/

# Run Ityfuzz
timeout $1 /app/ityfuzz/target/release/ityfuzz evm -t "${WORKDIR}/bench/*" --work-dir "${WORKDIR}/work_dir" -f > \
  $WORKDIR/stdout.txt 2>&1

mv $WORKDIR/work_dir $WORKDIR/output
mv $WORKDIR/stdout.txt $WORKDIR/output/stdout.txt
