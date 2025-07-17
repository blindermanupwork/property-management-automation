# HCP Sync Issues Report - Upcoming Reservations
*Generated: June 30, 2025*

## Overview
Analyzed 20 upcoming reservations (July 4-14, 2025) that don't have Service Job IDs in Airtable.

## Summary of Findings

### ✅ Successfully Matched (2 reservations)
- **5104 N 32nd St #324, Phoenix** - Job found and synced
- **2065 W 1st Pl, Mesa** - Job found but has duplicate Airtable records

### ❌ No HCP Jobs Found (18 reservations)
Most reservations simply don't have HCP jobs created yet.

## Detailed Analysis

### 1. Reservations With No Jobs (Need Creation)

| Property | Customer | Service Date | Source | Issue |
|----------|----------|--------------|---------|--------|
| 2824 N 82nd St, Scottsdale | Teresa Mayes | July 4 | Lodgify | No job exists |
| 5584 N 76th Pl, Scottsdale | Red Wheel VR | July 7 | Hospitable | No job exists |
| 8401 E Keim Dr, Scottsdale | Lance Farwick | July 7 | Hospitable | No job exists |
| 5950 N 78th St #123, Scottsdale | iTrip | July 9 | iTrip | No job exists |
| 4907 W Mercer Ln, Glendale | Angie Matthews | July 10 | VRBO | No job exists |
| 825 W Monterey Pl, Chandler | Ashley Pritchett | July 11 | Airbnb | No job exists |
| 15036 S 45th Pl, Phoenix | Brandon Passe | July 12 | Evolve | No job exists |
| 3600 Hayden Rd #2715, Scottsdale | Mevawala | July 12 | Airbnb | No job exists |
| 4643 W Burgess Ln, Laveen | Brianna Nuno | July 12 | Airbnb | No job exists |
| 6913 E Moreland St, Scottsdale | iTrip | July 13 | iTrip | No job exists (DO NOT CLEAN note) |
| 1057 E Butler Dr #1C, Phoenix | Ali Runyan | July 13 | Airbnb | No job exists |
| 819 N Granite St, Gilbert | Nicole Castillon | July 13 | Airbnb | No job exists |
| 3101 N 81st Pl, Scottsdale | Jake Luton | July 13 | Airbnb | No job exists |
| 8608 E Angus Dr, Scottsdale | Conner Doyle | July 13 | Airbnb | No job exists |
| 8438 E Keim Dr, Scottsdale | Lance Farwick | July 14 | Hospitable | No job exists |
| 26208 N 43rd Ct, Phoenix | iTrip | July 14 | iTrip | No job exists |

### 2. Address Issues

#### 🔴 Duplicate HCP Addresses
- **6934 E Sandra Terrace, Scottsdale**
  - Has 2 address IDs in HCP: `adr_f1cc30f3f20c47378b88eabfc885e96d` and `adr_d65ccf61872c4cc298dafd63f13f0bbc`
  - Already updated property to use `adr_d65ccf61872c4cc298dafd63f13f0bbc`

#### ✅ Correct Address IDs
All other properties have matching HCP Address IDs in Airtable.

### 3. Data Quality Issues

#### Duplicate Airtable Records
- **2065 W 1st Pl, Mesa (Kathy Nelson)**
  - 16 duplicate records for same reservation
  - 15 marked as "Old", 1 as "Modified"
  - Indicates Evolve import created duplicates

#### Special Cases
- **6913 E Moreland St** - Has note "DO NOT CLEAN OR DO INSPECTION"
- Several properties have "LONG TERM GUEST DEPARTING" flag (14+ day stays)
- Some have "Next Guest Unknown" vs specific next guest dates

## Recommendations

1. **Create Missing Jobs**
   - Use "Create Job & Sync Status" button for all 18 reservations without jobs
   - Pay attention to special instructions (e.g., DO NOT CLEAN)

2. **Fix Address Duplicates**
   - Resolve duplicate HCP addresses for 6934 E Sandra Terrace
   - Verify which address ID should be primary

3. **Clean Up Data**
   - Remove or consolidate duplicate Evolve import records
   - Standardize address formats between systems

4. **Update Reconciliation Script**
   - Script now matches by date only (not time)
   - Consider adding logic to handle duplicate addresses

5. **Process Order**
   - Start with earliest service dates (July 4)
   - Group by customer for efficiency (e.g., all iTrip properties)

## Next Steps

1. Run reconciliation script after creating jobs to verify matches
2. Monitor for new duplicate imports from Evolve
3. Consider automated job creation for reservations without conflicts