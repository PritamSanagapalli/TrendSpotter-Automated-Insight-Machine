#!/bin/bash

# TrendSpotter API - Test All Endpoints
# This script tests all API endpoints with KAG_conversion_data.csv

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"
CSV_FILE="KAG_conversion_data.csv"

echo -e "${BLUE}=========================================="
echo "TrendSpotter API - Endpoint Tests"
echo -e "==========================================${NC}\n"

# Check if CSV file exists
if [ ! -f "$CSV_FILE" ]; then
    echo -e "${RED}Error: $CSV_FILE not found!${NC}"
    exit 1
fi

echo -e "${GREEN}Using CSV file: $CSV_FILE${NC}\n"

# Test 1: Health Check
echo -e "${BLUE}=== Test 1: Health Check ===${NC}"
curl -s $API_URL/health | jq '.' 2>/dev/null || curl -s $API_URL/health
echo -e "\n"

# Test 2: Root Endpoint
echo -e "${BLUE}=== Test 2: Root Endpoint (API Info) ===${NC}"
curl -s $API_URL/ | jq '.' 2>/dev/null || curl -s $API_URL/
echo -e "\n"

# Test 3: Analyze Data (with AI - mandatory)
echo -e "${BLUE}=== Test 3: Analyze Data with AI Insights ===${NC}"
curl -s -X POST "$API_URL/analyze" \
  -F "file=@$CSV_FILE" \
  -F "contamination=0.05" | jq '.data.ai_analysis' 2>/dev/null || \
curl -s -X POST "$API_URL/analyze" \
  -F "file=@$CSV_FILE" \
  -F "contamination=0.05"
echo -e "\n"

# Test 4: Analyze with custom parameters (with AI)
echo -e "${BLUE}=== Test 4: Analyze with Custom Parameters + AI ===${NC}"
curl -s -X POST "$API_URL/analyze" \
  -F "file=@$CSV_FILE" \
  -F "contamination=0.1" \
  -F "z_thresh=2.5" \
  -F "iqr_factor=2.0" | jq '.data.anomaly_detection' 2>/dev/null || \
curl -s -X POST "$API_URL/analyze" \
  -F "file=@$CSV_FILE" \
  -F "contamination=0.1" \
  -F "z_thresh=2.5" \
  -F "iqr_factor=2.0"
echo -e "\n"

# Test 5: Generate PDF Report with AI (Simple Single Endpoint)
echo -e "${BLUE}=== Test 5: Generate PDF Report with AI Insights ===${NC}"
OUTPUT_PDF="report_$(date +%Y%m%d_%H%M%S).pdf"
curl -s -X POST "$API_URL/generate-report" \
  -F "file=@$CSV_FILE" \
  --output "$OUTPUT_PDF"

if [ -f "$OUTPUT_PDF" ]; then
    FILE_SIZE=$(ls -lh "$OUTPUT_PDF" | awk '{print $5}')
    echo -e "${GREEN}✓ PDF report with AI insights generated successfully!${NC}"
    echo -e "  File: $OUTPUT_PDF"
    echo -e "  Size: $FILE_SIZE"
    echo -e "  ${YELLOW}Open this PDF to see the AI-powered business analysis!${NC}"
else
    echo -e "${RED}✗ Failed to generate PDF${NC}"
fi
echo -e "\n"

# Test 6: Get JSON Response with AI (instead of PDF)
echo -e "${BLUE}=== Test 6: Get JSON Response with AI Analysis ===${NC}"
curl -s -X POST "$API_URL/upload-analyze-report" \
  -F "file=@$CSV_FILE" \
  -F "generate_pdf=false" | jq '.data.ai_analysis' 2>/dev/null || \
curl -s -X POST "$API_URL/upload-analyze-report" \
  -F "file=@$CSV_FILE" \
  -F "generate_pdf=false"
echo -e "\n"

# Summary
echo -e "${BLUE}=========================================="
echo "Test Summary"
echo -e "==========================================${NC}"
echo -e "${GREEN}✓ All tests completed!${NC}"
echo -e "\n${YELLOW}Note: AI analysis is enabled by default in all endpoints.${NC}"
echo -e "${YELLOW}Make sure GEMINI_API_KEY is set in .env for AI-powered insights.${NC}"
echo -e "\nGenerated files:"
ls -lh report_*.pdf 2>/dev/null || echo "  No reports generated"
echo -e "\n${YELLOW}Tip: Open the PDF files to see AI-powered business analysis!${NC}"
echo -e "${YELLOW}Tip: Visit http://localhost:8000/docs for interactive API docs${NC}\n"
