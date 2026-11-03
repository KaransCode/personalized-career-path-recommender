#!/usr/bin/env bash
# Simple curl-based smoke test for the full flow:
# upload -> get recommendations -> get skill gap
# Usage: ./test_flow.sh /path/to/resume.pdf "Data Scientist"

set -e
BASE_URL="${BASE_URL:-http://localhost:5000}"
RESUME_PATH="${1:-../data/sample_resumes/resume_1.pdf}"
TARGET_ROLE="${2:-Data Scientist}"

echo "1) Health check"
curl -s "$BASE_URL/health"
echo -e "\n"

echo "2) Uploading resume: $RESUME_PATH"
UPLOAD_RESPONSE=$(curl -s -F "file=@${RESUME_PATH}" "$BASE_URL/upload-resume")
echo "$UPLOAD_RESPONSE"
echo -e "\n"

CANDIDATE_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['candidate_id'])")
echo "Candidate ID: $CANDIDATE_ID"

echo -e "\n3) Fetching recommendations"
curl -s "$BASE_URL/recommendations/${CANDIDATE_ID}"
echo -e "\n"

echo -e "\n4) Fetching skill gap for role: $TARGET_ROLE"
curl -s "$BASE_URL/skill-gap/${CANDIDATE_ID}/${TARGET_ROLE}"
echo -e "\n"
