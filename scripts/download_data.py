"""Download the CUAD part of LegalBench-RAG from the Hugging Face mirror.

    python scripts/download_data.py            # into data/raw/
"""
import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw")
    args = ap.parse_args()
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Install dependencies first: pip install -r requirements.txt")
        return 1

    snapshot_download(
        repo_id="awinml/legalbench-rag",
        repo_type="dataset",
        allow_patterns=["benchmarks/cuad.json", "corpus/cuad/*"],
        local_dir=args.out,
    )
    out = Path(args.out)
    bench = out / "benchmarks" / "cuad.json"
    docs = list((out / "corpus" / "cuad").glob("*.txt"))
    print(f"benchmark file: {bench} (exists: {bench.exists()})")
    print(f"contract files: {len(docs)}")
    if not bench.exists() or not docs:
        print("Download looks incomplete: check the dataset layout on the Hub.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
