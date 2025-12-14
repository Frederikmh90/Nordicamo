# Two-Phase Processing Strategy - Stratified Sample

## 📊 Dataset Overview

### Phase 1: 10% Stratified Sample (READY NOW)
- **File**: `/work/NAMO_nov25/data/NAMO_10pct_stratified.parquet`
- **Size**: 73.6 MB
- **Articles**: 81,272 (exactly 10% from each outlet)
- **Outlets**: 57 alternative news media outlets
- **Time estimate**: ~1-2 days

### Phase 2: Remaining 90% (After Phase 1)
- **Articles**: ~731,728 remaining articles with domains
- **Time estimate**: ~9-12 days
- **Plus**: 140,846 articles without domain (~2 days)

## 🎯 Why Stratified Sampling?

✅ **Representative**: Every outlet gets equal representation
✅ **Balanced**: Large outlets don't dominate the sample
✅ **Testable**: Results from 10% can validate approach
✅ **Efficient**: Can analyze results before committing to full run

## 📈 Sample Breakdown by Outlet

**Top 10 outlets in sample:**
```
1. www.document.no      13,560 articles (10% of 135,609)
2. 180grader.dk         12,424 articles (10% of 124,244)
3. mvlehti.net           5,916 articles (10% of 59,166)
4. tidningensyre.se      5,418 articles (10% of 54,186)
5. swebbtv.se            3,440 articles (10% of 34,401)
6. nyadagbladet.se       3,271 articles (10% of 32,712)
7. samnytt.se            2,760 articles (10% of 27,600)
8. inyheter.no           2,754 articles (10% of 27,540)
9. bulletin.nu           2,738 articles (10% of 27,385)
10. denkorteavis.dk      2,720 articles (10% of 27,206)
```

**Plus 47 more outlets** (ranging from 13 to 2,699 articles each)

## 🚀 Phase 1: Process 10% Sample

### Step 1: Quick Test (100 articles, 2 minutes)

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25 && source venv/bin/activate

# Test with 100 articles
python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_10pct_stratified.parquet \
  --output data/test_100_stratified.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 100 \
  --checkpoint 100 \
  --max-articles 100

# Verify output
python3 << 'EOF'
import polars as pl
df = pl.read_parquet('data/test_100_stratified.parquet')
print(f"✅ Processed: {len(df)} articles")
print(f"\nOutlets in sample:")
print(df.group_by('domain').agg(pl.len().alias('count')).sort('count', descending=True))
print(f"\nCategories sample:")
print(df.select(['domain', 'categories', 'sentiment']).head(10))
EOF
```

### Step 2: Full 10% Sample (81K articles, ~1-2 days)

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25 && source venv/bin/activate

# Start Phase 1 processing
nohup python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_10pct_stratified.parquet \
  --output data/NAMO_10pct_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  > logs/nlp_phase1_$(date +%Y%m%d_%H%M%S).log 2>&1 &

echo "✅ Phase 1 started! Process ID: $!"
echo "📝 Log: logs/nlp_phase1_$(date +%Y%m%d_%H%M%S).log"
```

### Step 3: Monitor Phase 1

```bash
# Quick progress check
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 -c 'import polars as pl; df = pl.read_parquet(\"data/NAMO_10pct_enriched.parquet\"); print(f\"Progress: {len(df):,} / 81,272 ({100*len(df)/81272:.1f}%)\")' 2>/dev/null || echo 'No checkpoint yet'"

# Watch log
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "tail -f /work/NAMO_nov25/logs/nlp_phase1_*.log"

# Check GPU
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "nvidia-smi"
```

### Step 4: Download & Analyze Phase 1 Results

```bash
# Download results
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_10pct_enriched.parquet \
    ./data/nlp_enriched/

# Analyze locally
python3 << 'EOF'
import polars as pl

df = pl.read_parquet('data/nlp_enriched/NAMO_10pct_enriched.parquet')

print(f"📊 Phase 1 Results - 10% Sample")
print(f"="*60)
print(f"Total articles: {len(df):,}")
print(f"Outlets: {df['domain'].n_unique()}")
print()

# Category distribution across all outlets
print("Top 15 Categories:")
categories_flat = df['categories'].explode()
print(categories_flat.value_counts().head(15))
print()

# Sentiment distribution
print("Sentiment Distribution:")
print(df['sentiment'].value_counts())
print()

# Category distribution by outlet (top 5 outlets)
print("Categories by Top 5 Outlets:")
top_outlets = df.group_by('domain').agg(pl.len().alias('count')).sort('count', descending=True).head(5)
for outlet in top_outlets['domain']:
    outlet_df = df.filter(pl.col('domain') == outlet)
    cats = outlet_df['categories'].explode()
    print(f"\n{outlet} ({len(outlet_df):,} articles):")
    print(cats.value_counts().head(5))
EOF
```

## 🔄 Phase 2: Process Remaining Articles

After Phase 1 is complete and results look good:

### Step 1: Create Remaining Dataset

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25 && source venv/bin/activate

python3 << 'EOF'
import polars as pl

print("📂 Loading datasets...")
# Load original full dataset
full_df = pl.read_csv('data/NAMO_2025_09.csv', infer_schema_length=50000, ignore_errors=True)
full_with_domain = full_df.filter(pl.col('domain').is_not_null())

# Load Phase 1 processed URLs
phase1_df = pl.read_parquet('data/NAMO_10pct_enriched.parquet')
processed_urls = set(phase1_df['url'].to_list())

print(f"Full dataset: {len(full_with_domain):,} articles with domain")
print(f"Phase 1 processed: {len(processed_urls):,} articles")

# Get remaining articles
remaining_df = full_with_domain.filter(~pl.col('url').is_in(list(processed_urls)))

print(f"Remaining to process: {len(remaining_df):,} articles")
print()

# Save remaining
print("💾 Saving remaining articles...")
remaining_df.write_parquet('data/NAMO_remaining_90pct.parquet')

# Verify distribution
print("Distribution by outlet:")
print(remaining_df.group_by('domain').agg(pl.len().alias('count')).sort('count', descending=True).head(10))
EOF
```

### Step 2: Process Remaining 90%

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25 && source venv/bin/activate

# Start Phase 2 processing
nohup python3 scripts/02_nlp_batch_resume.py \
  --input data/NAMO_remaining_90pct.parquet \
  --output data/NAMO_remaining_enriched.parquet \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --batch-size 1000 \
  --checkpoint 1000 \
  > logs/nlp_phase2_$(date +%Y%m%d_%H%M%S).log 2>&1 &

echo "✅ Phase 2 started! Process ID: $!"
```

### Step 3: Combine Phase 1 & Phase 2

```bash
ssh -p 2693 ucloud@ssh.cloud.sdu.dk
cd /work/NAMO_nov25 && source venv/bin/activate

python3 << 'EOF'
import polars as pl

print("🔗 Combining Phase 1 and Phase 2...")
phase1 = pl.read_parquet('data/NAMO_10pct_enriched.parquet')
phase2 = pl.read_parquet('data/NAMO_remaining_enriched.parquet')

combined = pl.concat([phase1, phase2])

print(f"Phase 1: {len(phase1):,} articles")
print(f"Phase 2: {len(phase2):,} articles")
print(f"Combined: {len(combined):,} articles")

# Save combined
combined.write_parquet('data/NAMO_full_enriched.parquet')
print("✅ Saved to: data/NAMO_full_enriched.parquet")

# Summary stats
print()
print("Final Dataset Summary:")
print(f"  Total articles: {len(combined):,}")
print(f"  Outlets: {combined['domain'].n_unique()}")
print(f"  Categories:")
cats = combined['categories'].explode()
print(cats.value_counts().head(10))
EOF
```

## 📊 Quick Reference - Phase 1

```bash
# Start Phase 1 (10% sample)
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && nohup python3 scripts/02_nlp_batch_resume.py --input data/NAMO_10pct_stratified.parquet --output data/NAMO_10pct_enriched.parquet --model mistralai/Mistral-7B-Instruct-v0.3 --batch-size 1000 --checkpoint 1000 > logs/nlp_phase1.log 2>&1 &"

# Check Phase 1 progress
ssh -p 2693 ucloud@ssh.cloud.sdu.dk "cd /work/NAMO_nov25 && source venv/bin/activate && python3 -c 'import polars as pl; df = pl.read_parquet(\"data/NAMO_10pct_enriched.parquet\"); print(f\"{len(df):,} / 81,272\")' 2>/dev/null"

# Download Phase 1 results
scp -P 2693 ucloud@ssh.cloud.sdu.dk:/work/NAMO_nov25/data/NAMO_10pct_enriched.parquet ./data/nlp_enriched/
```

## ⏱️ Time Estimates

- **Phase 1 (81K articles)**: 1-2 days
- **Phase 2 (732K articles)**: 9-12 days  
- **Total**: 10-14 days

## ✅ Advantages of This Approach

1. **Early validation**: See results from all 57 outlets within 2 days
2. **Representative sample**: Every outlet equally represented
3. **Iterative**: Can adjust approach based on Phase 1 results
4. **Resume-friendly**: Each phase can be paused/resumed independently
5. **Analysis-ready**: Phase 1 provides immediate insights

---

**Ready to start Phase 1? Run the test (100 articles) first, then proceed with the full 10% sample!** 🚀

