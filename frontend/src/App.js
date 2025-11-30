import React, { useState } from 'react';
import axios from 'axios';

// API endpoint (Backend running on port 8001)
const API_BASE_URL = 'http://localhost:8001';

export default function App() {
  // State management
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp'];
      if (!validTypes.includes(file.type)) {
        setError('❌ Please select a valid image file (PNG, JPG, BMP)');
        setSelectedFile(null);
        setPreview(null);
        return;
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('❌ File size too large. Maximum 10MB allowed.');
        setSelectedFile(null);
        setPreview(null);
        return;
      }

      setSelectedFile(file);
      setError(null);

      // Generate preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // Handle drag and drop
  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
    event.dataTransfer.dropEffect = 'copy';
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect({ target: { files } });
    }
  };

  // Handle prediction
  const handleAnalyze = async () => {
    if (!selectedFile) {
      setError('❌ Please select an image first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(`${API_BASE_URL}/predict`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.status === 'success') {
        setResult(response.data);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Unknown error occurred';
      setError(`❌ Analysis failed: ${errorMsg}`);
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Get color based on diagnosis severity
  const getResultColor = () => {
    if (!result) return '#3b82f6';
    const diagnosis = result.diagnosis.toLowerCase();
    if (diagnosis === 'no dr') return '#10b981'; // Green
    if (diagnosis === 'mild') return '#f59e0b'; // Amber
    if (diagnosis === 'moderate') return '#ef6b42'; // Orange
    if (diagnosis === 'severe' || diagnosis === 'proliferative') return '#dc2626'; // Red
    return '#3b82f6';
  };

  // Styles
  const styles = {
    container: {
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    },
    header: {
      background: 'rgba(255, 255, 255, 0.95)',
      padding: '30px 20px',
      borderRadius: '12px',
      marginBottom: '30px',
      boxShadow: '0 10px 40px rgba(0, 0, 0, 0.1)',
      textAlign: 'center',
    },
    headerTitle: {
      fontSize: '32px',
      fontWeight: 'bold',
      color: '#1f2937',
      margin: '0 0 10px 0',
    },
    headerSubtitle: {
      fontSize: '14px',
      color: '#6b7280',
      margin: '0',
    },
    mainContent: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '30px',
      maxWidth: '1200px',
      margin: '0 auto',
    },
    column: {
      display: 'flex',
      flexDirection: 'column',
      gap: '20px',
    },
    card: {
      background: 'white',
      borderRadius: '12px',
      padding: '30px',
      boxShadow: '0 10px 40px rgba(0, 0, 0, 0.1)',
    },
    uploadArea: {
      border: '2px dashed #cbd5e1',
      borderRadius: '12px',
      padding: '40px 20px',
      textAlign: 'center',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      backgroundColor: '#f8fafc',
    },
    uploadAreaHover: {
      borderColor: '#667eea',
      backgroundColor: '#f0f4ff',
    },
    uploadText: {
      fontSize: '16px',
      color: '#6b7280',
      margin: '0 0 10px 0',
    },
    uploadIcon: {
      fontSize: '40px',
      marginBottom: '10px',
    },
    fileInput: {
      display: 'none',
    },
    previewImage: {
      width: '100%',
      maxHeight: '300px',
      objectFit: 'contain',
      borderRadius: '8px',
      marginBottom: '20px',
      border: '1px solid #e5e7eb',
    },
    fileName: {
      fontSize: '14px',
      color: '#6b7280',
      marginBottom: '15px',
      fontWeight: '500',
    },
    button: {
      padding: '12px 24px',
      fontSize: '16px',
      fontWeight: '600',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      width: '100%',
    },
    analyzeButton: {
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      fontSize: '16px',
      fontWeight: '600',
      padding: '14px 28px',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      width: '100%',
      marginTop: '10px',
    },
    analyzeButtonDisabled: {
      opacity: '0.6',
      cursor: 'not-allowed',
    },
    resultCard: {
      borderLeft: `6px solid ${getResultColor()}`,
      background: `rgba(${parseInt(getResultColor().slice(1, 3), 16)}, ${parseInt(getResultColor().slice(3, 5), 16)}, ${parseInt(getResultColor().slice(5, 7), 16)}, 0.05)`,
    },
    resultTitle: {
      fontSize: '24px',
      fontWeight: 'bold',
      color: getResultColor(),
      margin: '0 0 15px 0',
    },
    resultSeverity: {
      fontSize: '14px',
      color: '#6b7280',
      marginBottom: '10px',
      fontWeight: '500',
    },
    confidenceValue: {
      fontSize: '28px',
      fontWeight: 'bold',
      color: getResultColor(),
      marginBottom: '15px',
    },
    confidenceLabel: {
      fontSize: '14px',
      color: '#6b7280',
      marginBottom: '20px',
    },
    probabilityItem: {
      marginBottom: '15px',
    },
    probabilityLabel: {
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: '13px',
      fontWeight: '500',
      color: '#374151',
      marginBottom: '5px',
    },
    probabilityBar: {
      height: '8px',
      backgroundColor: '#e5e7eb',
      borderRadius: '4px',
      overflow: 'hidden',
    },
    probabilityFill: (percentage) => ({
      height: '100%',
      background: `linear-gradient(90deg, #667eea 0%, #764ba2 100%)`,
      width: `${percentage}%`,
      transition: 'width 0.5s ease',
    }),
    recommendationBox: {
      background: '#f0f9ff',
      border: '1px solid #7dd3fc',
      borderRadius: '8px',
      padding: '12px',
      marginTop: '15px',
      fontSize: '13px',
      color: '#0369a1',
      lineHeight: '1.5',
    },
    errorBox: {
      background: '#fee2e2',
      border: '1px solid #fca5a5',
      borderRadius: '8px',
      padding: '12px',
      color: '#991b1b',
      fontSize: '14px',
    },
    loadingSpinner: {
      display: 'inline-block',
      width: '20px',
      height: '20px',
      border: '3px solid #f3f4f6',
      borderTop: '3px solid #667eea',
      borderRadius: '50%',
      animation: 'spin 1s linear infinite',
    },
    noResultsText: {
      color: '#9ca3af',
      fontSize: '14px',
      textAlign: 'center',
      padding: '40px 20px',
    },
  };

  // Responsive layout for mobile
  const mainContentStyle = {
    ...styles.mainContent,
    '@media (max-width: 768px)': {
      gridTemplateColumns: '1fr',
    },
  };

  return (
    <div style={styles.container}>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
          body {
            margin: 0;
            padding: 0;
          }
        }
      `}</style>

      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.headerTitle}>🏥 DR Detection Dashboard</h1>
        <p style={styles.headerSubtitle}>AI-Powered Diabetic Retinopathy Detection System</p>
      </div>

      {/* Main Content */}
      <div style={mainContentStyle}>
        {/* Left Column: Upload & Control */}
        <div style={styles.column}>
          {/* Upload Area Card */}
          <div style={styles.card}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937', margin: '0 0 15px 0' }}>
              📁 Upload Retinal Image
            </h2>
            <div
              style={styles.uploadArea}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => document.getElementById('fileInput').click()}
            >
              <div style={styles.uploadIcon}>📷</div>
              <p style={styles.uploadText}>
                <strong>Click to upload</strong> or drag and drop
              </p>
              <p style={{ fontSize: '12px', color: '#9ca3af', margin: '0' }}>
                PNG, JPG, BMP • Max 10MB
              </p>
            </div>
            <input
              id="fileInput"
              type="file"
              style={styles.fileInput}
              onChange={handleFileSelect}
              accept="image/*"
            />

            {/* Preview */}
            {preview && (
              <>
                <img src={preview} alt="Preview" style={styles.previewImage} />
                <div style={styles.fileName}>
                  ✅ {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
                </div>
              </>
            )}

            {/* Error Message */}
            {error && <div style={styles.errorBox}>{error}</div>}

            {/* Analyze Button */}
            <button
              style={{
                ...styles.analyzeButton,
                ...(loading || !selectedFile ? styles.analyzeButtonDisabled : {}),
              }}
              onClick={handleAnalyze}
              disabled={loading || !selectedFile}
            >
              {loading ? (
                <>
                  <span style={styles.loadingSpinner}></span> Analyzing...
                </>
              ) : (
                '⚡ Analyze Image'
              )}
            </button>
          </div>

          {/* Info Card */}
          {!result && !loading && (
            <div style={styles.card}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', margin: '0 0 12px 0' }}>
                ℹ️ Instructions
              </h3>
              <ul
                style={{
                  fontSize: '13px',
                  color: '#6b7280',
                  lineHeight: '1.8',
                  margin: '0',
                  paddingLeft: '20px',
                }}
              >
                <li>Upload a retinal fundus image</li>
                <li>Click "Analyze Image" to run AI prediction</li>
                <li>Results will appear on the right panel</li>
                <li>High quality images work best</li>
              </ul>
            </div>
          )}
        </div>

        {/* Right Column: Results */}
        <div style={styles.column}>
          {result ? (
            <div style={{ ...styles.card, ...styles.resultCard }}>
              <h2 style={styles.resultTitle}>🔍 Analysis Result</h2>

              <div style={styles.resultSeverity}>
                Severity: <strong>{result.severity}</strong>
              </div>

              <div style={styles.confidenceValue}>{result.diagnosis}</div>
              <div style={styles.confidenceLabel}>
                Confidence: <strong>{(result.confidence * 100).toFixed(1)}%</strong>
              </div>

              {/* Probability Bars */}
              <div style={{ marginTop: '20px', marginBottom: '20px' }}>
                <h4
                  style={{
                    fontSize: '13px',
                    fontWeight: '600',
                    color: '#1f2937',
                    margin: '0 0 15px 0',
                  }}
                >
                  📊 Probability Distribution
                </h4>
                {Object.entries(result.probabilities).map(([className, probability]) => (
                  <div key={className} style={styles.probabilityItem}>
                    <div style={styles.probabilityLabel}>
                      <span>{className}</span>
                      <span>{(probability * 100).toFixed(1)}%</span>
                    </div>
                    <div style={styles.probabilityBar}>
                      <div
                        style={styles.probabilityFill(probability * 100)}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Recommendation */}
              <div style={styles.recommendationBox}>
                <strong>📋 Recommended Action:</strong>
                <div style={{ marginTop: '8px' }}>{result.recommended_action}</div>
              </div>

              {/* Reset Button */}
              <button
                style={{
                  ...styles.button,
                  background: '#f3f4f6',
                  color: '#374151',
                  marginTop: '20px',
                }}
                onClick={() => {
                  setResult(null);
                  setSelectedFile(null);
                  setPreview(null);
                  setError(null);
                }}
              >
                🔄 Analyze Another Image
              </button>
            </div>
          ) : (
            <div style={styles.card}>
              <div style={styles.noResultsText}>
                {loading ? (
                  <>
                    <div style={{ ...styles.loadingSpinner, margin: '20px auto' }}></div>
                    <p style={{ marginTop: '20px' }}>Analyzing retinal image...</p>
                    <p style={{ fontSize: '12px' }}>This may take a moment</p>
                  </>
                ) : (
                  <>
                    <p style={{ fontSize: '16px', marginBottom: '10px' }}>👈 Upload an image to get started</p>
                    <p style={{ fontSize: '12px' }}>Results will appear here</p>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          textAlign: 'center',
          marginTop: '40px',
          color: 'rgba(255, 255, 255, 0.7)',
          fontSize: '12px',
        }}
      >
        <p>
          🩺 Cyber-Physical Diabetic Retinopathy Detection System v1.0 | AI-Powered Diagnosis
        </p>
      </div>
    </div>
  );
}
