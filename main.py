from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import tempfile
import json
from datetime import datetime
from dotenv import load_dotenv
from extract_data import load_file
from anomaly_detector import detect_all
from gemini_generate import ask_gemini
from report_exporter import save_pdf_from_context, save_pptx_from_context
from pre_info import summarize_df
import pandas as pd
import numpy as np

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="TrendSpotter API",
    description="Event-driven data pipeline that converts raw CSV logs into executive-ready PDF reports with AI-generated narratives",
    version="1.0.0"
)

class AnalysisRequest(BaseModel):
    contamination: Optional[float] = 0.01
    z_thresh: Optional[float] = 3.0
    iqr_factor: Optional[float] = 1.5
    include_ai_analysis: Optional[bool] = True
    ai_model: Optional[str] = "gemini-2.5-flash"

class AnalysisResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    report_path: Optional[str] = None

@app.get("/")
async def root():
    return {
        "service": "TrendSpotter API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "upload_and_analyze": "/upload-analyze-report",
            "generate_report": "/generate-report (simple, single PDF output)"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_data(
    file: UploadFile = File(...),
    contamination: float = 0.01,
    z_thresh: float = 3.0,
    iqr_factor: float = 1.5,
    ai_model: str = "gemini-2.5-flash"
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        df = load_file(tmp_path)
        if isinstance(df, dict):
            df = list(df.values())[0] if df else pd.DataFrame()
        if df.empty:
            raise HTTPException(status_code=400, detail="Uploaded file contains no data")
        anomalies_df = detect_all(df)
        summary_stats = df.describe(include='all').to_dict()
        anomaly_counts = anomalies_df.sum().to_dict()
        response_data = {
            "file_info": {
                "filename": file.filename,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist()
            },
            "summary_statistics": summary_stats,
            "anomaly_detection": {
                "total_anomalies": int(anomalies_df['anomaly_any'].sum()),
                "anomaly_counts_by_method": anomaly_counts,
                "anomaly_percentage": float(anomalies_df['anomaly_any'].sum() / len(df) * 100)
            }
        }
        # AI Analysis is REQUIRED - Generate business insights
        try:
            if not os.getenv("GEMINI_API_KEY"):
                response_data["ai_analysis"] = "⚠️ GEMINI_API_KEY not configured. Please add your API key to .env file to get AI-powered business insights."
            else:
                anomaly_rows = df[anomalies_df['anomaly_any']]
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                
                # Prepare detailed context for business analysis
                total_anomalies = int(anomalies_df['anomaly_any'].sum())
                anomaly_pct = float(total_anomalies / len(df) * 100)
                
                # Get statistics for numeric columns
                stats_summary = []
                for col in num_cols[:8]:  # Top 8 numeric columns
                    col_mean = df[col].mean()
                    col_std = df[col].std()
                    col_min = df[col].min()
                    col_max = df[col].max()
                    
                    # Check if anomalies have different patterns
                    if total_anomalies > 0:
                        anomaly_mean = anomaly_rows[col].mean() if col in anomaly_rows.columns else col_mean
                        stats_summary.append(f"{col}: Overall avg={col_mean:.2f}, Anomaly avg={anomaly_mean:.2f}, Range=[{col_min:.2f}-{col_max:.2f}]")
                    else:
                        stats_summary.append(f"{col}: avg={col_mean:.2f}, std={col_std:.2f}, range=[{col_min:.2f}-{col_max:.2f}]")
                
                prompt = f"""You are a Senior Business Data Analyst helping business stakeholders understand their data.

Dataset Analysis:
- File: {file.filename}
- Total Records: {len(df):,}
- Columns: {', '.join(df.columns.tolist())}
- Anomalies Found: {total_anomalies:,} records ({anomaly_pct:.1f}% of data)

Key Metrics:
{chr(10).join(stats_summary)}

Your Task:
Provide a clear, actionable business report that explains:

1. **Data Overview**: What does this dataset represent and what are the key patterns?

2. **Anomaly Insights**: What anomalies were detected and what might be causing them? Are they concerning or expected variations?

3. **Business Impact**: How could these anomalies affect business operations, revenue, or decision-making?

4. **Recommendations**: What specific actions should the business team take based on these findings?

Write in clear, non-technical language that business stakeholders can understand. Be specific and actionable."""
                
                ai_response = ask_gemini(prompt, model=ai_model)
                response_data["ai_analysis"] = ai_response
        except Exception as e:
            response_data["ai_analysis"] = f"⚠️ AI analysis error: {str(e)}. Please check your GEMINI_API_KEY configuration."
        os.unlink(tmp_path)
        return AnalysisResponse(
            status="success",
            message="Analysis completed successfully",
            data=response_data
        )
    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/upload-analyze-report")
async def upload_analyze_and_report(
    file: UploadFile = File(...),
    contamination: float = 0.01,
    generate_pdf: bool = True,
    ai_model: str = "gemini-2.5-flash"
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        df = load_file(tmp_path)
        if isinstance(df, dict):
            df = list(df.values())[0] if df else pd.DataFrame()
        if df.empty:
            raise HTTPException(status_code=400, detail="Uploaded file contains no data")
        anomalies_df = detect_all(df)
        # AI Analysis - REQUIRED for business insights
        ai_analysis = ""
        if not os.getenv("GEMINI_API_KEY"):
            ai_analysis = "⚠️ GEMINI_API_KEY not configured. Add your API key to .env for AI-powered insights."
        else:
            try:
                anomaly_rows = df[anomalies_df['anomaly_any']]
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                
                # Create concise summary
                summary_lines = []
                summary_lines.append(f"Dataset: {len(df)} rows, {len(df.columns)} columns")
                summary_lines.append(f"Columns: {', '.join(df.columns.tolist()[:10])}")
                summary_lines.append(f"Anomalies detected: {int(anomalies_df['anomaly_any'].sum())} ({float(anomalies_df['anomaly_any'].sum() / len(df) * 100):.1f}%)")
                
                # Add key statistics  
                for col in num_cols[:5]:  # Only first 5 numeric columns
                    summary_lines.append(f"{col}: mean={df[col].mean():.2f}, std={df[col].std():.2f}")
                
                prompt = f"""You are a Senior Data Analyst writing an executive summary. Analyze:

{chr(10).join(summary_lines)}

Provide:
1. Overview of data quality and patterns
2. Analysis of anomalies and their potential causes
3. Business recommendations

Write in a professional tone. Keep it concise (3-4 paragraphs)."""
                
                ai_analysis = ask_gemini(prompt, model=ai_model)
            except Exception as e:
                ai_analysis = f"AI analysis unavailable: {str(e)}"
        report_context = {
            "title": f"TrendSpotter Analysis Report - {file.filename}",
            "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_info": {
                "filename": file.filename,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist()
            },
            "anomalies_summary": {
                "total": int(anomalies_df['anomaly_any'].sum()),
                "percentage": f"{anomalies_df['anomaly_any'].sum() / len(df) * 100:.2f}%"
            },
            "ai_analysis": ai_analysis
        }
        if generate_pdf:
            output_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            output_pdf.close()
            save_pdf_from_context(report_context, output_pdf.name)
            os.unlink(tmp_path)
            return FileResponse(
                output_pdf.name,
                media_type="application/pdf",
                filename=f"trendspotter_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
        else:
            os.unlink(tmp_path)
            return JSONResponse(content={
                "status": "success",
                "message": "Analysis completed",
                "data": report_context
            })
    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.post("/generate-report")
async def generate_report(
    file: UploadFile = File(...)
):
    """
    Simple endpoint: Upload CSV and get PDF report with AI insights.
    
    - **file**: CSV or SQLite database file
    
    AI analysis is automatically included to provide business insights.
    Returns: PDF file
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Load the data
        df = load_file(tmp_path)
        
        # Handle SQLite case
        if isinstance(df, dict):
            df = list(df.values())[0] if df else pd.DataFrame()
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Uploaded file contains no data")
        
        # Detect anomalies
        anomalies_df = detect_all(df)
        
        # AI Analysis - REQUIRED for business insights
        ai_analysis = ""
        if not os.getenv("GEMINI_API_KEY"):
            ai_analysis = "⚠️ GEMINI_API_KEY not configured. Add your API key to .env to enable AI-powered business insights."
        else:
            try:
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                anomaly_rows = df[anomalies_df['anomaly_any']]
                
                total_anomalies = int(anomalies_df['anomaly_any'].sum())
                anomaly_pct = float(total_anomalies / len(df) * 100)
                
                # Build detailed statistics
                stats_summary = []
                for col in num_cols[:8]:
                    col_mean = df[col].mean()
                    col_std = df[col].std()
                    
                    if total_anomalies > 0 and col in anomaly_rows.columns:
                        anomaly_mean = anomaly_rows[col].mean()
                        stats_summary.append(f"{col}: Normal={col_mean:.2f}, Anomaly={anomaly_mean:.2f}")
                    else:
                        stats_summary.append(f"{col}: mean={col_mean:.2f}, std={col_std:.2f}")
                
                prompt = f"""You are a Senior Business Data Analyst. Create an executive summary report.

Dataset: {file.filename}
Total Records: {len(df):,}
Columns: {', '.join(df.columns.tolist())}
Anomalies: {total_anomalies:,} ({anomaly_pct:.1f}%)

Key Metrics:
{chr(10).join(stats_summary)}

Provide a business-focused report:

1. **Overview**: What does this data tell us?
2. **Anomalies**: What unusual patterns exist? Why might they occur?
3. **Impact**: How do these findings affect business decisions?
4. **Actions**: What should the team do next?

Write clearly for business stakeholders. Focus on insights and actions."""
                
                ai_analysis = ask_gemini(prompt, model="gemini-2.5-flash")
            except Exception as e:
                ai_analysis = f"⚠️ AI error: {str(e)}"
        
        # Prepare report context
        report_context = {
            "title": f"Analysis Report - {file.filename}",
            "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_info": {
                "filename": file.filename,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist()
            },
            "anomalies_summary": {
                "total": int(anomalies_df['anomaly_any'].sum()),
                "percentage": f"{anomalies_df['anomaly_any'].sum() / len(df) * 100:.2f}%"
            },
            "ai_analysis": ai_analysis
        }
        
        # Generate PDF
        output_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        output_pdf.close()
        save_pdf_from_context(report_context, output_pdf.name)
        
        # Cleanup
        os.unlink(tmp_path)
        
        # Return PDF
        return FileResponse(
            output_pdf.name,
            media_type="application/pdf",
            filename=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
    
    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)