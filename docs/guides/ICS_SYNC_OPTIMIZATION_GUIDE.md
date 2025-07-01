# ICS Sync Performance Optimization Guide

## Current Performance Issues

Based on log analysis, the ICS sync process currently takes 3-5 minutes to complete, processing ~180-240 ICS feeds. The main bottlenecks are:

1. **Sequential API calls** - Each record check/update is done individually
2. **Duplicate detection** - Inefficient O(n²) duplicate checking for each event
3. **No caching** - Property mappings and existing records fetched every run
4. **Small batch sizes** - Only 10 records per batch for Airtable API
5. **Synchronous processing** - ICS parsing done sequentially despite async framework

## Optimization Strategies

### 1. **Increase Batch Sizes** (Quick Win)
```python
# Current
BatchCollector(reservations_table, batch_size=10, op="create")

# Optimized
BatchCollector(reservations_table, batch_size=100, op="create")
```
- Airtable supports up to 100 records per batch
- Reduces API calls by 10x

### 2. **Implement Caching**
```python
# Cache property mappings for 1 hour
property_cache = {}
property_cache_time = None
CACHE_DURATION = 3600  # 1 hour

def get_cached_property_mappings(ics_feeds_table):
    global property_cache, property_cache_time
    
    current_time = time.time()
    if property_cache_time and (current_time - property_cache_time) < CACHE_DURATION:
        return property_cache
    # ... fetch and cache
```

### 3. **Optimize Duplicate Detection**
```python
# Build index for O(1) lookups instead of O(n) searches
def build_duplicate_index(existing_records):
    duplicate_index = {}
    for records_list in existing_records.values():
        for record in records_list:
            if record["fields"].get("Status") in ("New", "Modified"):
                key = create_duplicate_key(...)
                duplicate_index[key] = record
    return duplicate_index
```

### 4. **Parallel ICS Processing**
```python
# Process multiple ICS feeds concurrently
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = []
    for url, ics_text in feeds:
        future = executor.submit(process_feed, url, ics_text, ...)
        futures.append(future)
    
    # Collect results
    for future in as_completed(futures):
        result = future.result()
```

### 5. **Connection Pooling**
```python
# Reuse connections for better performance
connector = aiohttp.TCPConnector(
    limit=100,  # Total connection limit
    limit_per_host=30,  # Per-host limit
    ttl_dns_cache=300  # DNS cache
)
```

### 6. **Smart Date Filtering**
```python
# Filter records at database level
cutoff_date = (date.today() - timedelta(days=180)).isoformat()
formula = f"OR({{Status}}='New', {{Status}}='Modified', {{Check-in Date}} >= '{cutoff_date}')"
```

### 7. **Reduce Field Fetching**
Only fetch required fields from Airtable:
```python
fields_to_fetch = [
    "Reservation UID", "ICS URL", "Check-in Date", "Check-out Date",
    "Status", "Entry Type", "Property ID", "Last Updated"
]
```

## Implementation Plan

### Phase 1: Quick Wins (30 min)
1. Increase batch sizes to 100
2. Add performance timing logs
3. Reduce fields fetched from Airtable

### Phase 2: Caching (1 hour)
1. Implement property mapping cache
2. Cache existing records for duplicate detection
3. Add cache invalidation logic

### Phase 3: Parallel Processing (2 hours)
1. Convert ICS parsing to ThreadPoolExecutor
2. Implement connection pooling
3. Add rate limiting to prevent API throttling

### Phase 4: Database Optimization (1 hour)
1. Add formula-based filtering
2. Implement bulk operations
3. Optimize duplicate detection algorithm

## Expected Performance Improvements

- **Batch size increase**: 50-70% reduction in API calls
- **Caching**: 20-30% reduction in startup time
- **Parallel processing**: 40-60% reduction in ICS parsing time
- **Connection pooling**: 30-40% reduction in network overhead
- **Overall**: 60-80% reduction in total sync time (from 3-5 min to 30-60 seconds)

## Monitoring

Add performance metrics:
```python
class PerformanceTimer:
    def __init__(self, name):
        self.name = name
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        logging.info(f"⏱️ {self.name} took {elapsed:.2f} seconds")

# Usage
with PerformanceTimer("Fetching existing records"):
    records = get_existing_records()
```

## Testing

1. **Backup current script**: `cp icsProcess.py icsProcess_backup.py`
2. **Test in dev first**: `AUTOMATION_ENV=dev python3 icsProcess_optimized.py`
3. **Compare results**: Ensure same number of records created/updated
4. **Monitor performance**: Check logs for timing improvements
5. **Gradual rollout**: Test with subset of feeds first

## Rollback Plan

If issues occur:
```bash
# Restore original script
cp icsProcess_backup.py icsProcess.py

# Or use Git
git checkout HEAD -- icsProcess.py
```

## Additional Optimizations (Future)

1. **Redis caching**: Store frequently accessed data in Redis
2. **Database views**: Create Airtable views for common queries
3. **Incremental sync**: Only process changed ICS feeds
4. **Event streaming**: Use webhooks instead of polling
5. **Distributed processing**: Split feeds across multiple workers