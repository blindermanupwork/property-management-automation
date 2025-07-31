# Service Line Description Differences

## Critical Differences Found

### 1. Same-Day Format (MAJOR)
- **❌ Current Airtable Script**: `${serviceType} STR SAME DAY`
- **✅ Codebase (HCP Sync & API)**: `SAME DAY ${serviceType} STR`

Example:
- Wrong: `Turnover STR SAME DAY`
- Correct: `SAME DAY Turnover STR`

### 2. Owner Arriving Logic (MAJOR)
- **❌ Current Airtable Script**: Adds "OWNER ARRIVING" as a separate part in the hierarchy
- **✅ Codebase**: When next entry is a block, includes "OWNER ARRIVING" in the base service name

Example when owner is arriving on July 3:
- Wrong: `Custom text - OWNER ARRIVING - Turnover STR Next Guest July 3`
- Correct: `Custom text - OWNER ARRIVING Turnover STR July 3`

### 3. Long-Term Guest with Owner Arriving
- **❌ Current Airtable Script**: Always adds "LONG TERM GUEST DEPARTING" if stay >= 14 days
- **✅ Codebase**: Only adds "LONG TERM GUEST DEPARTING" if owner is NOT already in the base name

Example when long-term guest is departing and owner is arriving:
- Wrong: `LONG TERM GUEST DEPARTING - OWNER ARRIVING Turnover STR July 3`
- Correct: `OWNER ARRIVING Turnover STR July 3` (long-term guest flag omitted)

## Service Line Hierarchy (Correct)

1. **Custom Instructions** (max 200 chars)
2. **LONG TERM GUEST DEPARTING** (only if stay >= 14 days AND owner not in base name)
3. **Base service name** which can be:
   - `SAME DAY ${serviceType} STR` (for same-day turnovers)
   - `OWNER ARRIVING ${serviceType} STR ${month} ${day}` (when next entry is block)
   - `${serviceType} STR Next Guest ${month} ${day}` (normal next guest)
   - `${serviceType} STR Next Guest Unknown` (no next guest found)

## Examples

### Same-Day Turnover
- Correct: `SAME DAY Turnover STR`
- Wrong: `Turnover STR SAME DAY`

### Owner Arriving with Custom Instructions
- Correct: `Please check hot tub - OWNER ARRIVING Turnover STR July 3`
- Wrong: `Please check hot tub - OWNER ARRIVING - Turnover STR Next Guest July 3`

### Long-Term Guest Without Owner
- Correct: `Check all towels - LONG TERM GUEST DEPARTING - Turnover STR Next Guest July 5`
- Wrong: Would be the same in this case

### Long-Term Guest With Owner Arriving
- Correct: `OWNER ARRIVING Turnover STR July 3`
- Wrong: `OWNER ARRIVING - LONG TERM GUEST DEPARTING - Turnover STR Next Guest July 3`

## Fix Applied

The fixed script (`update-service-line-description-fixed.js`) now:
1. Places "SAME DAY" at the beginning for same-day turnovers
2. Includes "OWNER ARRIVING" in the base service name when next entry is a block
3. Only adds "LONG TERM GUEST DEPARTING" when owner is not already in the base name
4. Maintains the same hierarchy and formatting as the codebase