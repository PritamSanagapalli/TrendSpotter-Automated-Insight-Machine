import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def detect_outliers_univariate_zscore(df, z_thresh=3.0):
    """Detect outliers using Z-score method. Handles constant columns."""
    df_num = df.select_dtypes(include=[np.number])
    if df_num.shape[1] == 0:
        return None
    
    # Calculate std, handle zero std
    std = df_num.std(ddof=0)
    std = std.replace(0, np.nan)  # Replace 0 std with NaN to avoid division by zero
    
    z = (df_num - df_num.mean()) / std
    z = z.fillna(0)  # Fill NaN (from constant columns) with 0
    
    return (z.abs() > z_thresh)

def detect_outliers_iqr(df, factor=1.5):
    """Detect outliers using IQR method. Handles edge cases."""
    df_num = df.select_dtypes(include=[np.number])
    if df_num.shape[1] == 0:
        return None
    
    Q1 = df_num.quantile(0.25)
    Q3 = df_num.quantile(0.75)
    IQR = Q3 - Q1
    
    # Handle zero IQR (constant columns)
    IQR = IQR.replace(0, np.nan)
    
    lower = Q1 - factor * IQR
    upper = Q3 + factor * IQR
    
    outliers = (df_num < lower) | (df_num > upper)
    return outliers.fillna(False)

def detect_multivariate_outliers_iforest(df, contamination=0.01, random_state=0):
    df_num = df.select_dtypes(include=[np.number]).fillna(0)
    if df_num.shape[1] == 0:
        return None
    clf = IsolationForest(contamination=contamination, random_state=random_state)
    clf.fit(df_num.values)
    preds = clf.predict(df_num.values)  
    return pd.Series(preds == -1, index=df.index, name='anomaly_iforest')

def detect_multivariate_outliers_iforest(df, contamination=0.01, random_state=0):
    """Detect multivariate outliers using Isolation Forest. Robust to dirty data."""
    df_num = df.select_dtypes(include=[np.number])
    
    if df_num.shape[1] == 0:
        return None
    
    # Handle missing values and infinite values
    df_num = df_num.replace([np.inf, -np.inf], np.nan)
    df_num = df_num.fillna(0)
    
    # Remove constant columns (zero variance)
    df_num = df_num.loc[:, df_num.std() > 0]
    
    if df_num.shape[1] == 0:
        return None
    
    # Ensure we have enough samples
    n_samples = len(df_num)
    if n_samples < 2:
        return pd.Series([False] * n_samples, index=df.index, name='anomaly_iforest')
    
    try:
        clf = IsolationForest(contamination=contamination, random_state=random_state)
        clf.fit(df_num.values)
        preds = clf.predict(df_num.values)
        return pd.Series(preds == -1, index=df.index, name='anomaly_iforest')
    except Exception as e:
        print(f"Warning: Isolation Forest failed: {e}")
        return None

def detect_local_density_outliers_lof(df, n_neighbors=20, contamination='auto'):
    """Detect outliers using Local Outlier Factor. Robust to dirty data."""
    df_num = df.select_dtypes(include=[np.number])
    
    if df_num.shape[1] == 0:
        return None
    
    # Handle missing and infinite values
    df_num = df_num.replace([np.inf, -np.inf], np.nan)
    df_num = df_num.fillna(0)
    
    # Remove constant columns
    df_num = df_num.loc[:, df_num.std() > 0]
    
    if df_num.shape[1] == 0:
        return None
    
    # Ensure n_neighbors is valid
    n_samples = len(df_num)
    if n_samples < 2:
        return pd.Series([False] * n_samples, index=df.index, name='anomaly_lof')
    
    n_neighbors = min(n_neighbors, n_samples - 1)
    
    try:
        lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
        preds = lof.fit_predict(df_num.values)
        return pd.Series(preds == -1, index=df.index, name='anomaly_lof')
    except Exception as e:
        print(f"Warning: LOF failed: {e}")
        return None

def detect_cluster_distance_outliers(df, n_clusters=5, threshold_percentile=95):
    df_num = df.select_dtypes(include=[np.number]).fillna(0)
    if df_num.shape[1] == 0 or len(df_num) < n_clusters:
        return None
    scaler = StandardScaler()
    X = scaler.fit_transform(df_num.values)
    kmeans = KMeans(n_clusters=n_clusters, random_state=0)
    labels = kmeans.fit_predict(X)
    centroids = kmeans.cluster_centers_
    dists = np.linalg.norm(X - centroids[labels], axis=1)
    threshold = np.percentile(dists, threshold_percentile)
    return pd.Series(dists > threshold, index=df.index, name='anomaly_cluster_dist')

def detect_cluster_distance_outliers(df, n_clusters=5, threshold_percentile=95):
    """Detect outliers using K-Means cluster distance. Robust to dirty data."""
    df_num = df.select_dtypes(include=[np.number])
    
    if df_num.shape[1] == 0:
        return None
    
    # Handle missing and infinite values
    df_num = df_num.replace([np.inf, -np.inf], np.nan)
    df_num = df_num.fillna(0)
    
    # Remove constant columns
    df_num = df_num.loc[:, df_num.std() > 0]
    
    if df_num.shape[1] == 0:
        return None
    
    # Ensure we have enough samples
    n_samples = len(df_num)
    if n_samples < n_clusters:
        n_clusters = max(2, n_samples // 2)  # Use fewer clusters if needed
    
    if n_samples < 2:
        return pd.Series([False] * n_samples, index=df.index, name='anomaly_cluster_dist')
    
    try:
        scaler = StandardScaler()
        X = scaler.fit_transform(df_num.values)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
        labels = kmeans.fit_predict(X)
        centroids = kmeans.cluster_centers_
        
        dists = np.linalg.norm(X - centroids[labels], axis=1)
        threshold = np.percentile(dists, threshold_percentile)
        
        return pd.Series(dists > threshold, index=df.index, name='anomaly_cluster_dist')
    except Exception as e:
        print(f"Warning: Cluster distance failed: {e}")
        return None

def detect_all(df):
    """
    Run all anomaly detection methods on the dataframe.
    Handles dirty data, missing values, and edge cases robustly.
    """
    if df.empty:
        return pd.DataFrame()
    
    results = {}
    
    # Z-score detection
    try:
        z = detect_outliers_univariate_zscore(df, z_thresh=3.0)
        if z is not None and not z.empty:
            results['outlier_zscore'] = z.any(axis=1)  # Any column flagged
    except Exception as e:
        print(f"Warning: Z-score detection failed: {e}")
    
    # IQR detection
    try:
        iqr = detect_outliers_iqr(df, factor=1.5)
        if iqr is not None and not iqr.empty:
            results['outlier_iqr'] = iqr.any(axis=1)  # Any column flagged
    except Exception as e:
        print(f"Warning: IQR detection failed: {e}")
    
    # Isolation Forest
    try:
        iso = detect_multivariate_outliers_iforest(df, contamination=0.01, random_state=0)
        if iso is not None:
            results['anomaly_iforest'] = iso
    except Exception as e:
        print(f"Warning: Isolation Forest detection failed: {e}")
    
    # Local Outlier Factor
    try:
        lof = detect_local_density_outliers_lof(df, n_neighbors=20, contamination='auto')
        if lof is not None:
            results['anomaly_lof'] = lof
    except Exception as e:
        print(f"Warning: LOF detection failed: {e}")
    
    # Cluster distance
    try:
        clust = detect_cluster_distance_outliers(df, n_clusters=5, threshold_percentile=95)
        if clust is not None:
            results['anomaly_cluster_dist'] = clust
    except Exception as e:
        print(f"Warning: Cluster distance detection failed: {e}")
    
    # If no methods succeeded, return empty dataframe with anomaly_any column
    if not results:
        return pd.DataFrame({'anomaly_any': [False] * len(df)}, index=df.index)
    
    res_df = pd.DataFrame(results, index=df.index)
    
    # Fill any NaN values with False
    res_df = res_df.fillna(False)
    
    # Mark as anomaly if at least 2 methods agree
    res_df['anomaly_any'] = res_df.sum(axis=1) >= 2
    
    return res_df
    
if __name__ == "__main__":
    df = pd.read_csv("your_data.csv")  
    anomalies = detect_all(df)
    print("Anomaly detection summary:")
    print(anomalies.sum())  
    df_with_flags = pd.concat([df, anomalies], axis=1)
    df_with_flags.to_csv("data_with_anomaly_flags.csv", index=False)
    print("Saved flagged data to data_with_anomaly_flags.csv")