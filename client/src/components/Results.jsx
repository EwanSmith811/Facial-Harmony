import React from 'react';
import { Popover } from '@headlessui/react';

export default function Results({ data, summary, getColorClass, featureDescriptions }) {
  const features = data.features;
  const average = (Object.values(features).reduce((a, b) => a + b, 0) / Object.values(features).length).toFixed(1);

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
            <div className="flex justify-between items-center">
              <Popover className="relative">
                <Popover.Button className="text-gray-700 font-medium hover:text-indigo-600 transition-colors">
                  {feature}
                </Popover.Button>
                
                <Popover.Panel className="absolute z-10 p-3 bg-white rounded-lg shadow-lg text-sm max-w-xs border border-gray-100">
                  {featureDescriptions[feature]}
                </Popover.Panel>
              </Popover>
              <span className="text-gray-600 font-medium">{score}/10</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${getColorClass(score)}`}
                style={{ width: `${(score/10)*100}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>

      {summary && (
        <div className="mt-8 p-6 bg-indigo-50 rounded-xl border border-indigo-100">
          <h3 className="text-lg font-semibold text-indigo-700 mb-3">AI Analysis Summary</h3>
          <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{summary}</p>
        </div>
      )}
    </div>
  );
}