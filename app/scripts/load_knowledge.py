"""
Load the FAQ knowledge base into ChromaDB.

Usage:
    uv run python -m app.scripts.load_knowledge
    uv run python -m app.scripts.load_knowledge --csv data/faq.csv
"""

import argparse
import sys

from app.services.knowledge_service import load_faq


def main():
    parser = argparse.ArgumentParser(description="Load FAQ CSV into ChromaDB")
    parser.add_argument("--csv", default="data/faq.csv", help="Path to FAQ CSV file")
    args = parser.parse_args()

    try:
        count = load_faq(args.csv)
        print(f"Successfully loaded {count} FAQ entries.")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
