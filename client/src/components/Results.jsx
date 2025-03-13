import React from 'react';
import { Popover } from '@headlessui/react';
import PropTypes from 'prop-types';

export default function Results({ data, summary, getColorClass, featureDescriptions }) {
  // Add safety checks
  const features = data?.features || {};
  const average = data ? 
    (Object.values(features).reduce((a, b) => a + b, 0) / Object.values(features).length || 0).toFixed(1) 
    : '0.0';

  return (
    <div className="space-y-8">
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-center shadow-xl">
        <h2 className="text-2xl font-bold text-white mb-2">Overall Score</h2>
        <div className="text-6xl font-black text-white mb-2">{average}</div>
        <p className="text-indigo-100 font-medium">Comprehensive Facial Assessment</p>
      </div>

      <div className="space-y-6">
        {Object.entries(features).map(([feature, score]) => (
          <div key={feature} className="space-y-2">
            {/* Add null check for score */}
            <div className="flex justify-between items-center">
              <Popover className="relative">
                <Popover.Button className="text-gray-700 font-medium hover:text-indigo-600 transition-colors">
                  {feature}
                </Popover.Button>
                <Popover.Panel className="absolute z-10 p-3 bg-white rounded-lg shadow-lg text-sm max-w-xs border border-gray-100">
                  {featureDescriptions[feature] || 'No description available'}
                </Popover.Panel>
              </Popover>
              <span className="text-gray-600 font-medium">
                {typeof score === 'number' ? score.toFixed(1) : 'N/A'}/10
              </span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${getColorClass(score)}`}
                style={{ width: `${((score || 0)/10)*100}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>

      {/* Add fallback for empty summary */}
      {summary && (
        <div className="mt-8 p-6 bg-indigo-50 rounded-xl border border-indigo-100">
          <h3 className="text-lg font-semibold text-indigo-700 mb-3">AI Analysis Summary</h3>
          <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
            {summary || 'No summary available'}
          </p>
        </div>
      )}
    </div>
  );
}

Results.propTypes = {
  data: PropTypes.shape({
    features: PropTypes.object,
    imgPath: PropTypes.string
  }),
  summary: PropTypes.string,
  getColorClass: PropTypes.func.isRequired,
  featureDescriptions: PropTypes.object.isRequired
};