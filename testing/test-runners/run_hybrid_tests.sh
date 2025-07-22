#!/bin/bash
# Script to run both ICS and CSV hybrid processing tests

echo "=================================="
echo "HYBRID PROCESSING TEST RUNNER"
echo "=================================="
echo "Running at: $(date)"
echo ""

# Set working directory
cd /home/opc/automation

# Make test scripts executable
chmod +x test_ics_hybrid.py
chmod +x test_csv_hybrid.py

# Run ICS tests
echo "Running ICS hybrid processing tests..."
echo "=================================="
python3 test_ics_hybrid.py
ICS_RESULT=$?

echo ""
echo ""

# Run CSV tests
echo "Running CSV hybrid processing tests..."
echo "=================================="
python3 test_csv_hybrid.py
CSV_RESULT=$?

echo ""
echo "=================================="
echo "TEST SUMMARY"
echo "=================================="

if [ $ICS_RESULT -eq 0 ]; then
    echo "✅ ICS Tests: PASSED"
else
    echo "❌ ICS Tests: FAILED"
fi

if [ $CSV_RESULT -eq 0 ]; then
    echo "✅ CSV Tests: PASSED"
else
    echo "❌ CSV Tests: FAILED"
fi

echo ""

# Overall result
if [ $ICS_RESULT -eq 0 ] && [ $CSV_RESULT -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi