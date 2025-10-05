# Sync Training Cache to Windows GPU Machine

Once Mac finishes collecting training data and creates the cache, follow these steps to sync it to Windows for GPU training.

## Step 1: Wait for Mac Cache Collection to Complete

Monitor progress:
```bash
tail -f cache_test.log | grep -E "Collected|Saved.*cache|Training"
```

When you see "Saved X samples to cache", the cache is ready.

## Step 2: Commit and Push Cache-Related Code

On Mac:
```bash
# The cache file itself is gitignored, but the code changes are committed
git push
```

## Step 3: Update Windows Repo

On Windows (via SSH from Mac):
```bash
# Pull latest code with cache system
ssh ruben@192.168.1.117 'wsl bash -c "cd ~/repos/invest && git pull"'
```

## Step 4: Copy Cache File to Windows

**Method 1: SCP (Recommended)**
```bash
# From Mac - copy cache file to Windows
scp neural_network/training/training_data_cache.json \
    ruben@192.168.1.117:~/repos/invest/neural_network/training/
```

**Method 2: Manual via WSL**
```bash
# From Mac - get cache content
cat neural_network/training/training_data_cache.json | pbcopy

# On Windows WSL - paste and save
ssh ruben@192.168.1.117
wsl
cd ~/repos/invest/neural_network/training
cat > training_data_cache.json
# Paste content (Ctrl+V), then Ctrl+D to finish
```

## Step 5: Verify Cache on Windows

```bash
ssh ruben@192.168.1.117 'wsl bash -c "ls -lh ~/repos/invest/neural_network/training/training_data_cache.json"'
```

Should show the cache file with size > 0.

## Step 6: Test Cache Loading on Windows

```bash
# Run training - should load from cache instantly
ssh ruben@192.168.1.117 'wsl bash -c "cd ~/repos/invest && setsid bash ./neural_network/training/start_gpu_training.sh > training.log 2>&1 < /dev/null &"'

# Check log - should see "Using cached training data"
ssh ruben@192.168.1.117 'wsl bash -c "tail -20 ~/repos/invest/comprehensive_training.log"'
```

If you see `✅ Using cached training data` and `Loaded X samples from cache`, the cache is working!

## Step 7: Start Full Training on Windows GPU

Now you can increase target_samples and train with GPU:

1. Edit `neural_network/training/comprehensive_neural_training.py` on Windows
2. Change `target_samples: int = 500` to `target_samples: int = 10000`
3. Run training with GPU

The cache will be reused if config matches. If you want fresh data, delete the cache file or set `use_cache=False`.

## Troubleshooting

**Cache not loading**:
- Check file exists: `ls neural_network/training/training_data_cache.json`
- Check config matches: start_year, end_year, target_samples must match cache
- Check logs for "Cache config mismatch" message

**Want to force fresh data collection**:
```python
# In comprehensive_neural_training.py
TrainingConfig(
    ...
    use_cache=False  # Disable cache
)
```
