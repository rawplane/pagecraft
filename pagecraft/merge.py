"""PDF creation: convert inputs and merge into a single PDF.

Phase 2: parallel conversion via ProcessPoolExecutor + streaming merge
(lazy generator) so peak RAM stays low even for 500+ files.
"""

import io
import multiprocessing
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

import img2pdf
from PIL import UnidentifiedImageError
from pypdf import PdfReader, PdfWriter
from tqdm import tqdm

from pagecraft.constants import SUPPORTED_HTML_EXTENSIONS
from pagecraft.converters import build_layout_fun


def _worker_init() -> None:
    """Pre-import heavy modules once per worker process.

    Each spawn-ed worker would otherwise pay the ~1.7s WeasyPrint
    import cost on its first HTML job. Pre-importing here amortizes
    that cost across all jobs the worker handles. For image-only
    batches this is wasted, but the import is cheap when WeasyPrint
    is not actually used for rendering.
    """
    try:
        import weasyprint  # noqa: F401 — pre-warm import
    except Exception:
        pass  # WeasyPrint optional for image-only batches


def _get_pool_context():
    """Return the multiprocessing context appropriate for this platform.

    On Linux we use the default 'fork' (fast, no re-import cost, the
    fork() deprecation warning from PIL is benign for our use case
    because the parent is only multi-threaded due to fontconfig/Cairo
    internal threads, not Python threads holding locks). On macOS /
    Windows we use 'spawn' (the only safe option) and rely on
    _worker_init to amortize import cost.
    """
    if sys.platform == "win32" or sys.platform == "darwin":
        return multiprocessing.get_context("spawn")
    # Linux: fork is far faster than spawn (no re-import of WeasyPrint).
    return multiprocessing.get_context("fork")


def is_html_file(file_path: Path) -> bool:
    return file_path.suffix.lower() in SUPPORTED_HTML_EXTENSIONS


def convert_one(
    input_path: Path, page_size: str
) -> Tuple[Optional[bytes], Optional[str]]:
    """Convert a single input file to PDF bytes.

    Must be top-level + picklable for ProcessPoolExecutor.
    Returns (pdf_bytes, None) on success or (None, error_message) on failure.
    All exceptions are caught here so a worker crash doesn't kill the pool.
    """
    try:
        if is_html_file(input_path):
            # Import WeasyPrint lazily so the parent process doesn't pay
            # its ~1.7s import cost unless HTML is actually present.
            from weasyprint import HTML

            buffer = io.BytesIO()
            HTML(
                filename=str(input_path), base_url=str(input_path.parent)
            ).write_pdf(buffer)
            return buffer.getvalue(), None

        layout_fun = build_layout_fun(page_size)
        with open(input_path, "rb") as f:
            img_data = f.read()
        if layout_fun:
            pdf_bytes = img2pdf.convert(img_data, layout_fun=layout_fun)
        else:
            pdf_bytes = img2pdf.convert(img_data)
        return pdf_bytes, None

    except PermissionError:
        return None, f"Permission denied: {input_path}"
    except UnidentifiedImageError:
        return None, f"Invalid or corrupted image: {input_path}"
    except img2pdf.ImageFormatError as e:
        return None, f"Unsupported image format {input_path}: {e}"
    except Exception as e:
        return None, f"Error converting {input_path}: {e}"


def convert_all(
    input_files: List[Path],
    page_size: str,
    jobs: Optional[int] = None,
    quiet: bool = False,
) -> Iterator[Tuple[Path, Optional[bytes], Optional[str]]]:
    """Lazily convert all input files in parallel.

    Yields (path, pdf_bytes_or_None, error_or_None) tuples as each
    conversion finishes (order is not guaranteed). The caller consumes
    them one at a time, so peak memory stays ~1 segment instead of N.
    """
    if jobs is None:
        jobs = os.cpu_count() or 2

    # For very small batches or when only 1 job is requested,
    # skip the pool overhead and run serially.
    if jobs <= 1 or len(input_files) <= 1:
        for p in input_files:
            pdf_bytes, err = convert_one(p, page_size)
            yield p, pdf_bytes, err
        return

    ctx = _get_pool_context()
    with ProcessPoolExecutor(
        max_workers=jobs,
        mp_context=ctx,
        initializer=_worker_init,
    ) as ex:
        futures = {
            ex.submit(convert_one, p, page_size): p for p in input_files
        }
        for fut in as_completed(futures):
            p = futures[fut]
            try:
                pdf_bytes, err = fut.result()
            except Exception as e:
                # Should not happen (convert_one catches everything),
                # but guard against pool-level failures.
                pdf_bytes, err = None, f"Worker error {p}: {e}"
            yield p, pdf_bytes, err


def _is_all_images(input_files: List[Path]) -> bool:
    """True if every input is an image (no HTML)."""
    return all(not is_html_file(p) for p in input_files)


def _fast_path_all_images(
    input_files: List[Path],
    output_path: str,
    page_size: str,
    quiet: bool,
) -> int:
    """Fast path for image-only batches: img2pdf can natively merge
    many images into a single PDF in one call, skipping the per-file
    PDF-then-pypdf-merge pipeline entirely. This is ~30-50% faster
    for large image-only batches.

    Returns the number of files successfully written.
    Falls back to the slow path (returns -1) if the fast path fails
    at the pool level, so the caller can retry.
    """
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    layout_fun = build_layout_fun(page_size)
    kwargs = {"layout_fun": layout_fun} if layout_fun else {}

    try:
        with open(output_path, "wb") as out:
            img2pdf.convert(
                [str(p) for p in input_files],
                outputstream=out,
                **kwargs,
            )
    except Exception as e:
        # Fast path failed (e.g. one corrupt image). Fall back to the
        # slow path which tolerates per-file failures.
        if not quiet:
            print(
                f"Fast path failed ({e}); retrying with per-file conversion...",
                file=sys.stderr,
            )
        return -1

    if not quiet:
        print(f"Success! PDF created: {output_path}")
        print(f"Total files processed: {len(input_files)}")
    return len(input_files)


def create_pdf(
    input_files: List[Path],
    output_path: str,
    page_size: str,
    jobs: Optional[int] = None,
    quiet: bool = False,
) -> None:
    if not input_files:
        print("Error: No valid input files to convert", file=sys.stderr)
        sys.exit(1)

    n_images = sum(1 for p in input_files if not is_html_file(p))
    n_html = len(input_files) - n_images
    if not quiet:
        print(
            f"Processing {len(input_files)} file(s) "
            f"({n_images} image(s), {n_html} HTML) "
            f"with {jobs or (os.cpu_count() or 2)} job(s)..."
        )

    # Fast path: image-only batches skip pypdf merge entirely.
    # Only worth it for small batches (<=20 files): for larger batches
    # the parallel slow path is faster because img2pdf.convert(list)
    # is itself single-threaded.
    FAST_PATH_THRESHOLD = 20
    if n_html == 0 and len(input_files) <= FAST_PATH_THRESHOLD:
        count = _fast_path_all_images(
            input_files, output_path, page_size, quiet
        )
        if count >= 0:
            return  # Success via fast path.
        # count == -1: fast path failed, fall through to slow path.

    writer = PdfWriter()
    n_success = 0
    n_failed = 0

    iterator = convert_all(input_files, page_size, jobs=jobs, quiet=quiet)
    if not quiet:
        iterator = tqdm(
            iterator,
            total=len(input_files),
            desc="Converting",
            unit="file",
        )

    for path, pdf_bytes, err in iterator:
        if pdf_bytes is None:
            print(f"Warning: {err}", file=sys.stderr)
            n_failed += 1
            continue
        # Stream directly into the writer: this segment is released
        # from memory once its pages are appended.
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)
        n_success += 1

    if n_success == 0:
        print("Error: Failed to convert any input files", file=sys.stderr)
        sys.exit(1)

    try:
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            writer.write(f)

        if not quiet:
            print(f"\nSuccess! PDF created: {output_path}")
            print(f"Total files processed: {n_success}")
            if n_failed:
                print(f"Skipped (failed): {n_failed}", file=sys.stderr)

    except PermissionError:
        print(
            f"Error: Permission denied writing to {output_path}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error creating PDF: {e}", file=sys.stderr)
        sys.exit(1)
