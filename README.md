# 🚀 TrendSpotter API

### Author: Pritam Sanagapalli | SRM University-AP
> **An event-driven data pipeline API that converts raw CSV logs into executive-ready PDF reports with AI-generated narratives in under 30 seconds.**

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
##  Overview

TrendSpotter is a production-ready API that automates data analysis and reporting. Upload a CSV file, and get back a comprehensive analysis with:

- **Statistical summaries** of your data
- **Anomaly detection** using multiple ML algorithms (Isolation Forest, LOF, Z-Score, IQR, K-Means)
- **AI-powered insights** from Google Gemini 2.5 Flash
- **Professional PDF reports** ready for executives

##  Key Features

- ✅ **Multiple Anomaly Detection Methods**: Isolation Forest, Local Outlier Factor, Z-Score, IQR, Cluster Distance
- ✅ **AI-Generated Analysis**: Google Gemini 2.5 Flash provides expert-level insights
- ✅ **REST API**: Easy integration with any application
- ✅ **Docker Support**: One-command deployment
- ✅ **PDF Report Generation**: Professional, branded reports
- ✅ **Fast**: Polars & NumPy for high-performance data processing

##  Tech Stack

| Component | Technology |
|-----------|-----------|
| **API Framework** | FastAPI |
| **Data Processing** | Pandas, Polars |
| **ML/Anomaly Detection** | Scikit-Learn |
| **AI Model** | Google Gemini 2.5 Flash |
| **Report Generation** | WeasyPrint, Jinja2 |

## Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API Key

### Setup & Run

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Create `.env` file:**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. **Run the API:**
```bash
python3 main.py
```

4. **API is now running at:** `http://localhost:8000`
   - Interactive docs: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`

### Quick Start Script

Alternatively, use the provided script:
```bash
chmod +x start.sh
./start.sh
```

### Available Endpoints

#### 1. Health Check
```bash
GET /health
```
Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-03T10:30:00"
}
```

#### 2. Analyze Data (JSON Response)
```bash
POST /analyze
```

**Parameters:**
- `file` (required): CSV or SQLite file
- `contamination` (optional, default: 0.01): Isolation Forest contamination parameter
- `z_thresh` (optional, default: 3.0): Z-score threshold
- `iqr_factor` (optional, default: 1.5): IQR factor
- `include_ai_analysis` (optional, default: true): Whether to include AI analysis
- `ai_model` (optional, default: "gemini-2.5-flash"): Gemini model to use

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@your_data.csv" \
  -F "contamination=0.01" \
  -F "include_ai_analysis=true"
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/analyze"
files = {"file": open("your_data.csv", "rb")}
data = {
    "contamination": 0.01,
    "include_ai_analysis": True
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

#### 3. Upload, Analyze & Generate PDF Report
```bash
POST /upload-analyze-report
```

**Parameters:**
- `file` (required): CSV or SQLite file
- `contamination` (optional, default: 0.01)
- `generate_pdf` (optional, default: true)
- `include_ai_analysis` (optional, default: true)
- `ai_model` (optional, default: "gemini-2.5-flash")

**Example:**
```bash
curl -X POST "http://localhost:8000/upload-analyze-report" \
  -F "file=@your_data.csv" \
  -F "generate_pdf=true" \
  --output report.pdf
```

**Example using Python:**
```python
import requests

url = "http://localhost:8000/upload-analyze-report"
files = {"file": open("your_data.csv", "rb")}
data = {"generate_pdf": True, "include_ai_analysis": True}

response = requests.post(url, files=files, data=data)

# Save PDF
with open("report.pdf", "wb") as f:
    f.write(response.content)
```

## 📊 How It Works

```mermaid
graph LR
    A[Upload CSV] --> B[Extract Data]
    B --> C[Detect Anomalies]
    C --> D[AI Analysis]
    D --> E[Generate Report]
    E --> F[PDF/JSON Response]
```

### 1. **Data Extraction** (`extract_data.py`)
- Supports CSV and SQLite files
- Automatic format detection

### 2. **Anomaly Detection** (`anomaly_detector.py`)
- **Z-Score**: Statistical outlier detection
- **IQR**: Interquartile range method
- **Isolation Forest**: Unsupervised ML anomaly detection
- **Local Outlier Factor (LOF)**: Density-based outlier detection
- **K-Means Cluster Distance**: Distance from cluster centroids

### 3. **AI Analysis** (`gemini_generate.py`)
- Uses Google Gemini 2.5 Flash
- Generates human-readable insights
- Strict context adherence (no hallucinations)

### 4. **Report Generation** (`report_exporter.py`)
- HTML/CSS templating with Jinja2
- PDF conversion with WeasyPrint
- Professional formatting

##  Configuration

Edit `.env` file:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
API_HOST=0.0.0.0
API_PORT=8000
DEFAULT_CONTAMINATION=0.01
DEFAULT_Z_THRESH=3.0
DEFAULT_IQR_FACTOR=1.5
```

##  Testing the API

### Using curl:
```bash
# Health check
curl http://localhost:8000/health

# Analyze data
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@sample_data.csv"

# Generate PDF report
curl -X POST "http://localhost:8000/upload-analyze-report" \
  -F "file=@sample_data.csv" \
  --output report.pdf
```

### Using Python requests:
```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Analyze
files = {"file": open("sample_data.csv", "rb")}
response = requests.post("http://localhost:8000/analyze", files=files)
print(response.json())
```

##  Project Structure

```
groundTruthProject/
├── main.py                  # FastAPI application
├── extract_data.py          # Data extraction module
├── anomaly_detector.py      # ML anomaly detection
├── gemini_generate.py       # AI analysis with Gemini
├── report_exporter.py       # PDF report generation
├── pre_info.py             # Data summarization
├── test_api.py             # API test suite
├── requirements.txt         # Python dependencies
├── start.sh                # Quick start script
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

##  Troubleshooting

### Issue: "Import 'fastapi' could not be resolved"
**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: "GEMINI_API_KEY not found"
**Solution:** Set environment variable:
```bash
export GEMINI_API_KEY="your_key_here"
```

### Issue: WeasyPrint dependencies missing
**Solution:** Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangoft2-1.0-0 libcairo2

# macOS
brew install pango cairo
```

##  Learnings & Challenges Overcome

1. **AI Hallucination Prevention**: Implemented strict context system prompts
2. **Docker Networking**: Configured proper SMTP ports and environment variables
3. **Performance**: Chose Polars over Pandas for 10x faster processing
4. **Production-Ready**: Error handling, validation, and proper API design
