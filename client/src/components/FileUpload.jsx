import React, { useState, useRef } from 'react';
import axios from 'axios';
import Results from './Results';

export default function FileUpload() {
  const [results, setResults] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  // Feature descriptions for tooltips
  const featureDescriptions = {
    'Symmetry': 'Measures facial symmetry between left and right sides',
    'Canthal Tilt': 'Angle of eye corners affecting youthful appearance',
    'Golden Ratio': 'Proximity to ideal 1.618:1 facial proportions',
    'Buccal Fat': 'Cheek fat volume affecting facial contour',
    'Jawline': 'Definition and angularity of jaw structure',
    'Skin Clarity': 'Evenness and smoothness of skin texture',
    'Under-Eye': 'Dark circles or puffiness under eyes',
    'Philtrum Ratio': 'Proportion between nose and upper lip'
  };

  // Determine color class based on score
  const getColorClass = (score) => {
    if (score < 4) return 'bg-red-400';
    if (score < 7) return 'bg-yellow-400';
    return 'bg-green-400';
  };

  // Handle file selection
  const handleFileSelect = async (e) => {
    setError('');
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPEG, PNG, etc.).');
      return;
    }

    // Validate file size (4MB limit)
    if (file.size > 4 * 1024 * 1024) {
      setError('File size must be less than 4MB.');
      return;
    }

    // Preview the image
    const reader = new FileReader();
    reader.onload = (e) => setUploadedImage(e.target.result);
    reader.readAsDataURL(file);
    setSelectedFile(file);
  };

  // Handle analysis request
  const handleAnalyze = async () => {
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Step 1: Upload and analyze the image
      const analysisRes = await axios.post(
        `${process.env.REACT_APP_API_URL}/api/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          validateStatus: (status) => status === 200 // Only treat 200 as success
        }
      );

      // Verify response structure
      if (!analysisRes.data?.features || !analysisRes.data?.imgPath) {
        throw new Error('Invalid response format from server');
      }

      // Step 2: Generate AI summary
      const summaryRes = await axios.post(
        `${process.env.REACT_APP_API_URL}/api/generate-summary`,
        { scores: analysisRes.data.features },
        {
          validateStatus: (status) => status === 200
        }
      );

      // Verify summary exists
      if (!summaryRes.data?.summary) {
        throw new Error('Failed to generate summary');
      }

      // Update state with validated results
      setResults({
        ...analysisRes.data,
        imgPath: `${process.env.REACT_APP_API_URL}${analysisRes.data.imgPath}`
      });
      setSummary(summaryRes.data.summary);

    } catch (err) {
      let errorMessage = 'Analysis failed. Please try again.';
      if (err.response) {
        errorMessage = err.response.data?.error || errorMessage;
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      setResults(null);
      setSummary('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-4xl font-bold mb-6 text-center bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
          Facial Analysis
          <span className="block text-lg font-normal mt-3 text-gray-500">
            Upload a photo for comprehensive analysis
          </span>
        </h1>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* Image preview */}
        {uploadedImage && (
          <div className="mb-8 border-4 border-indigo-50 rounded-xl overflow-hidden">
            <img 
              src={uploadedImage} 
              alt="Upload preview" 
              className="w-full max-h-96 object-contain"
              aria-label="Uploaded image preview"
            />
          </div>
        )}

        {/* File input and buttons */}
        <div className="flex flex-col items-center gap-4 mb-8">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            accept="image/*"
            aria-label="Select image file"
          />
          <button
            onClick={() => fileInputRef.current.click()}
            className="px-6 py-3 bg-indigo-100 text-indigo-700 rounded-lg font-semibold hover:bg-indigo-200 transition-colors"
            aria-label={uploadedImage ? 'Change photo' : 'Select photo'}
          >
            {uploadedImage ? 'Change Photo' : 'Select Photo'}
          </button>
          
          {uploadedImage && (
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
              aria-label={loading ? 'Analyzing image' : 'Start analysis'}
            >
              {loading ? (
                <>
                  <span className="inline-block mr-2">Analyzing...</span>
                  <span className="animate-spin">🌀</span>
                </>
              ) : 'Start Analysis'}
            </button>
          )}
        </div>

        {/* Loading state */}
        {loading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Processing facial features...</p>
          </div>
        )}

        {/* Results component */}
        {results && (
          <Results 
            data={results} 
            summary={summary}
            getColorClass={getColorClass}
            featureDescriptions={featureDescriptions}
          />
        )}
      </div>
    </div>
  );
}