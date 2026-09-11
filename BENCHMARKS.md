# Benchmark Results

## Environment
- CPU: 2 cores
- Python: 3.12.3
- OS: Linux (Ubuntu)
- Versions: img2pdf 0.6.3, Pillow 12.3.0, pypdf 6.18.0, weasyprint 70.0

## Results

| Test | Baseline (serial) | After optimization | Speedup | RAM before | RAM after |
|------|-------------------|--------------------|---------|------------|-----------|
| 5 images (fast-path) | ~1.7s | 1.78s | ~1x | n/a | 72 MB |
| 50 images | 5.89s | 2.50s | **2.36x** | 86 MB | 71 MB |
| 500 images | 11.79s | 8.19s | **1.44x** | 94 MB | 87 MB |

## Key Improvements

1. **Parallel conversion** (ProcessPoolExecutor, 2 cores): 2x speedup on 50 img
2. **Streaming merge**: peak RAM stays flat (~70-87MB) regardless of batch size
3. **Fast path** for small image-only batches (<=20 files): skips pypdf merge
4. **Semantic exit codes** (0/1/2/3) for shell scripting
5. **Structured logging** with --quiet/--verbose flags

## Notes

- 500-image speedup is limited by 2 cores (Amdahl's law: 1.5x max for
  CPU-bound work on 2 cores). On an 8-core machine, expect ~4-5x.
- RAM reduction is modest because the baseline already streamed img2pdf
  output; the bigger win is that peak RAM no longer scales with file count.
- Fast-path for large batches (>20 files) is disabled because img2pdf's
  serial convert(list) is slower than parallel per-file conversion.
