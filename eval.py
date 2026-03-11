import os
import csv

PROJECTS = sorted(["2_a4j", "5_templateit", "4_rif", "1_tullibee", "3_jigen"])

OUTPUT_ORIGINALS = ["original-trial-1", "original-trial-2", "original-trial-3"]
OUTPUT_MODIFIEDS = ["muse-trial-1", "muse-trial-2", "muse-trial-3"]

def find_stats_files(directory):
    csv_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv"):
                csv_files.append(os.path.join(root, file))
    return csv_files

def get_cov(filepath):
    with open(filepath) as f:
        reader = csv.reader(f)
        next(reader)
        row = next(reader)
        covered = int(row[4])
        branches = int(row[3])
        return branches, covered

def is_valid(filepath):
    tests_exist = False
    d = os.path.dirname(filepath)
    for root, dirs, files in os.walk(d):
        for f in files:
            if f.endswith("_ESTest.java"):
                content = open(os.path.join(root, f)).read()
                if "EvoSuite did not generate any tests" in content:
                    return False, "no_tests_generated"
                else:
                    tests_exist = True

    if not tests_exist:
        return False, "no_test_file"
    return True, "ok"

def avg_cov(base_dirs, proj, ref_file, ref_base_dir, require_all=False):
    covered_sum = 0
    branches_val = None
    count = 0
    for base_dir in base_dirs:
        f = ref_file.replace(
            os.path.join(ref_base_dir, proj),
            os.path.join("outputs", base_dir, proj)
        )

        valid = os.path.exists(f) and is_valid(f)[0]
        if not valid:
            if require_all:
                count += 1  # count this run as 0 covered
            continue

        try:
            b, c = get_cov(f)
        except Exception:
            if require_all:
                count += 1
            continue

        if branches_val is None:
            branches_val = b
        elif b != branches_val:
            if require_all:
                count += 1
            continue

        covered_sum += c
        count += 1

    if count == 0 or branches_val is None:
        return None, None, 0

    return branches_val, covered_sum / count, count



total_branches_muse = 0
total_covered_muse  = 0
total_branches_og  = 0
total_covered_og   = 0
methods_compared   = 0
skipped            = 0

REF_ORIGINAL = os.path.join("outputs", OUTPUT_ORIGINALS[0])

print(f"{'Project':<15} {'Methods':>10}  {'branches':>10} {'OG Cov':>10} {'MUSE Cov':>10} {'Change':>10}")
print("-" * 80)

for proj in PROJECTS:
    ref_dir = os.path.join(REF_ORIGINAL, proj)

    if not os.path.isdir(ref_dir):
        print(f"  WARNING: {ref_dir} not found, skipping.")
        continue

    csv_files = find_stats_files(ref_dir)
    proj_branches_og = proj_covered_og = proj_branches_mod = proj_covered_mod = 0
    proj_compared = proj_skipped = 0
    #print(f"  [{proj}] found {len(csv_files)} csv files in {ref_dir}")

    for ref_file in sorted(csv_files):
        method = os.path.basename(os.path.dirname(ref_file))
        
        #branches, coverages, total number of trials found
        branches_og, coverage_og_avg, og_count = avg_cov(OUTPUT_ORIGINALS, proj, ref_file, REF_ORIGINAL, require_all=True)
        branches_muse, coverage_muse_avg, muse_count = avg_cov(OUTPUT_MODIFIEDS, proj, ref_file, REF_ORIGINAL)

        if muse_count < 3:  # require all 3 MUSE trials to be valid
            proj_skipped += 1
            skipped += 1
            continue

        #branches_og, coverage_og_avg, og_count = avg_cov(OUTPUT_ORIGINALS, proj, ref_file, REF_ORIGINAL)
        #branches_muse, coverage_muse_avg, muse_count = avg_cov(OUTPUT_MODIFIEDS, proj, ref_file, REF_ORIGINAL)

        if branches_muse is None: # or muse_count < 3:
            proj_skipped += 1
            skipped += 1
            continue

        if branches_og is None:
            # No valid original runs — treat as 0 coverage baseline
            branches_og = branches_muse
            coverage_og_avg = 0.0

        if branches_og != branches_muse:
            print(f"  SKIP (branch mismatch): {method} og={branches_og} mod={branches_muse}")
            proj_skipped += 1
            skipped += 1
            continue

        pct_og  = coverage_og_avg  / branches_og if branches_og > 0 else 0.0
        pct_mod = coverage_muse_avg / branches_muse if branches_muse > 0 else 0.0
        delta   = pct_mod - pct_og

        total_branches_og  += branches_og
        total_covered_og   += coverage_og_avg
        total_branches_muse += branches_muse
        total_covered_muse  += coverage_muse_avg
        methods_compared   += 1

        proj_branches_og  += branches_og
        proj_covered_og   += coverage_og_avg
        proj_branches_mod += branches_muse
        proj_covered_mod  += coverage_muse_avg
        proj_compared     += 1

    p_og  = proj_covered_og  / proj_branches_og  if proj_branches_og  > 0 else 0.0
    p_mod = proj_covered_mod / proj_branches_mod if proj_branches_mod > 0 else 0.0
    chg   = (p_mod - p_og) * 100 
    print(f"{proj:<15} {proj_compared:>11}  {proj_branches_og:>10} {proj_covered_og:>8.1f} {proj_covered_mod:>9.1f} {chg:>+7.2f}%")
    #print(f"{proj:<15} {proj_compared:>10} {proj_skipped:>10} {proj_branches_og:>10} {proj_covered_og:>10} {proj_covered_mod:>10} {chg:>+9.2f}%")

print("-" * 110)
if total_branches_og > 0 and total_branches_muse > 0:
    overall_og  = total_covered_og  / total_branches_og
    overall_muse = total_covered_muse / total_branches_muse
    improvement = (overall_muse - overall_og)  * 100
    print(f"\nMethods compared: {methods_compared}")
    print(f"Original EvoSuite coverage: {overall_og:.4f} ({total_covered_og:.1f}/{total_branches_og} branches)")
    print(f"Modified EvoSuite coverage: {overall_muse:.4f} ({total_covered_muse:.1f}/{total_branches_muse} branches)")
    print(f"Improvement: {improvement:+.2f}%")
