import React, { useState, useRef } from 'react';
import axios from 'axios';
import Results from './Results';

export default function FileUpload() {
  const [results, setResults] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState('');
  const fileInputRef = useRef(null);

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

  const getColorClass = (score) => {
    if (score < 4) return 'bg-red-400';
    if (score < 7) return 'bg-yellow-400';
    return 'bg-green-400';
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => setUploadedImage(e.target.result);
    reader.readAsDataURL(file);
    setSelectedFile(file);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // First get facial analysis results
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      // Then get AI summary
      const summaryResponse = await axios.post('http://localhost:5000/api/generate-summary', {
        scores: response.data.features
      });
      setSummary(summaryResponse.data.summary);
    } catch (error) {
      alert('Analysis failed: ' + error.message);
    }
    setLoading(false);
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

        {uploadedImage && (
          <div className="mb-8 border-4 border-indigo-50 rounded-xl overflow-hidden">
            <img 
              src={uploadedImage} 
              alt="Upload preview" 
              className="w-full max-h-96 object-contain"
            />
          </div>
        )}

        <div className="flex flex-col items-center gap-4 mb-8">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            accept="image/*"
          />
          <button
            onClick={() => fileInputRef.current.click()}
            className="px-6 py-3 bg-indigo-100 text-indigo-700 rounded-lg font-semibold hover:bg-indigo-200 transition-colors"
          >
            {uploadedImage ? 'Change Photo' : 'Select Photo'}
          </button>
          
          {uploadedImage && (
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {loading ? 'Analyzing...' : 'Start Analysis'}
            </button>
          )}
        </div>

        {loading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Processing facial features...</p>
          </div>
        )}

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