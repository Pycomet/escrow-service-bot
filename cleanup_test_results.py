#!/usr/bin/env python3
"""
Web3 Test Results Cleanup Utility
=================================

This script cleans up old test result files, keeping only the most recent ones.

Usage:
    python cleanup_test_results.py [--keep N] [--dry-run]

Options:
    --keep N       Number of recent files to keep (default: 3)
    --dry-run      Show what would be deleted without actually deleting
    --all          Remove all test result files
    --help         Show this help message

Examples:
    python cleanup_test_results.py                    # Keep 3 most recent
    python cleanup_test_results.py --keep 5           # Keep 5 most recent
    python cleanup_test_results.py --dry-run          # Preview what would be deleted
    python cleanup_test_results.py --all              # Remove all result files
"""

import argparse
import glob
import os
from datetime import datetime


def cleanup_test_results(keep_count=3, dry_run=False, remove_all=False):
    """Clean up old test result files"""

    # Define patterns for test result files
    patterns = [
        "web3_comprehensive_test_report_*.html",
        "web3_comprehensive_test_results_*.json",
        "wallet_generation_test_results_*.json",
        "balance_checking_test_results_*.json",
        "transaction_simulation_test_results_*.json",
    ]

    # Exclude 'latest' files from cleanup
    exclude_patterns = ["*_latest.*"]

    total_found = 0
    total_to_remove = 0

    print(f"🧹 Web3 Test Results Cleanup Utility")
    print("=" * 50)

    if remove_all:
        print("⚠️  Mode: Remove ALL test result files")
    elif dry_run:
        print(f"👀 Mode: Dry run (preview only, keeping {keep_count} most recent)")
    else:
        print(f"🗑️  Mode: Remove old files (keeping {keep_count} most recent)")

    print("=" * 50)

    for pattern in patterns:
        files = glob.glob(pattern)

        # Filter out 'latest' files
        files = [
            f for f in files if not any(exclude in f for exclude in exclude_patterns)
        ]

        if not files:
            continue

        total_found += len(files)
        print(f"\n📁 Pattern: {pattern}")
        print(f"   Found: {len(files)} files")

        if remove_all:
            files_to_remove = files
        elif len(files) > keep_count:
            # Sort by modification time, newest first
            files.sort(key=os.path.getmtime, reverse=True)
            files_to_remove = files[keep_count:]
        else:
            files_to_remove = []
            print(f"   Action: Keeping all (≤ {keep_count} files)")
            continue

        if files_to_remove:
            total_to_remove += len(files_to_remove)
            print(
                f"   Action: {'Would remove' if dry_run else 'Removing'} {len(files_to_remove)} files"
            )

            for file_path in files_to_remove:
                file_age = datetime.fromtimestamp(os.path.getmtime(file_path))
                size_kb = os.path.getsize(file_path) / 1024

                if dry_run:
                    print(
                        f"     - {file_path} ({size_kb:.1f}KB, {file_age.strftime('%Y-%m-%d %H:%M')})"
                    )
                else:
                    try:
                        os.remove(file_path)
                        print(f"     ✅ {file_path} ({size_kb:.1f}KB)")
                    except OSError as e:
                        print(f"     ❌ Failed to remove {file_path}: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("📊 CLEANUP SUMMARY")
    print("=" * 50)
    print(f"Total files found: {total_found}")
    print(f"Files {'to be removed' if dry_run else 'removed'}: {total_to_remove}")
    print(f"Files kept: {total_found - total_to_remove}")

    if dry_run and total_to_remove > 0:
        print("\n💡 To actually remove these files, run without --dry-run")
    elif total_to_remove == 0:
        print("\n✅ No cleanup needed!")
    else:
        print(f"\n🎉 Cleanup completed! Freed up disk space.")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up old Web3 test result files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Keep 3 most recent files
  %(prog)s --keep 5           # Keep 5 most recent files  
  %(prog)s --dry-run          # Preview what would be deleted
  %(prog)s --all              # Remove all result files
        """,
    )

    parser.add_argument(
        "--keep",
        type=int,
        default=3,
        help="Number of recent files to keep (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--all", action="store_true", help="Remove all test result files"
    )

    args = parser.parse_args()

    if args.all and args.keep != 3:
        print("❌ Error: --all and --keep cannot be used together")
        return 1

    try:
        cleanup_test_results(
            keep_count=args.keep, dry_run=args.dry_run, remove_all=args.all
        )
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
