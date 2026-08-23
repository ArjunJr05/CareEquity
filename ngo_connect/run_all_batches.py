"""
run_all_batches.py
------------------
Runs all five batch scripts in order, then geocodes the full dataset
and prints final stats.

Usage:  python run_all_batches.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_master_csv import geocode_all, save_csv, print_stats, load_csv

BATCHES = [
    "batch01_AL_to_GA",
    "batch02_HI_to_MD",
    "batch03_MA_to_NJ",
    "batch04_NM_to_SC",
    "batch05_SD_to_DC",
]

def run_batch(module_name):
    import importlib
    print(f"\n{'='*60}")
    print(f"  Running {module_name} ...")
    print(f"{'='*60}")
    mod = importlib.import_module(module_name)
    from build_master_csv import append_rows
    rows_added = append_rows(mod.ROWS)
    print(f"  {module_name}: {len(mod.ROWS)} rows submitted")
    return rows_added

if __name__ == "__main__":
    t0 = time.time()

    all_rows = []
    for batch in BATCHES:
        all_rows = run_batch(batch)
        time.sleep(1)   # brief pause between batches

    print(f"\n{'='*60}")
    print("  All batches loaded. Running final geocoding pass ...")
    print(f"{'='*60}")
    all_rows = load_csv()
    all_rows = geocode_all(all_rows)
    save_csv(all_rows)

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  COMPLETE in {elapsed/60:.1f} minutes")
    print_stats(all_rows)
    print(f"{'='*60}")
