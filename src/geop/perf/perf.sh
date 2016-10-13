#!/bin/bash
set -e
set -x

for size in "lrg" "med" "sm"; do
    python -m timeit -s "import perf" "perf.read_${size}_1024_none()"
    python -m timeit -s "import perf" "perf.read_${size}_512_none()"
    python -m timeit -s "import perf" "perf.read_${size}_256_none()"
    python -m timeit -s "import perf" "perf.read_${size}_512_lzw()"
    python -m timeit -s "import perf" "perf.read_${size}_256_lzw()"
    python -m timeit -s "import perf" "perf.read_${size}_256_pb()"
done

for size in "lrg" "med" "sm"; do
    python -m timeit -s "import perf_tile as perf" "perf.read_${size}_1024_none()"
    python -m timeit -s "import perf_tile as perf" "perf.read_${size}_512_none()"
    python -m timeit -s "import perf_tile as perf" "perf.read_${size}_256_none()"
    python -m timeit -s "import perf_tile as perf" "perf.read_${size}_512_lzw()"
    python -m timeit -s "import perf_tile as perf" "perf.read_${size}_256_lzw()"
    python -m timeit -s "import perf_tile as perf" "perf.read_${size}_256_pb()"
done
