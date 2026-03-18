import React from 'react';

const AIDev: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">AI Development Lab</h2>
        <p className="text-gray-600 mb-6">
          Code analysis, optimization suggestions, and AI-powered development tools.
        </p>
        
        {/* Code Workbench */}
        <div className="border border-gray-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Code Workbench</h3>
          <div className="border border-gray-300 rounded-md bg-gray-900 h-64 p-4 font-mono text-sm text-green-400 overflow-x-auto">
            <pre>{`# Example Python code
def analyze_portfolio(assets):
    total_value = sum(asset['value'] for asset in assets)
    risk_score = calculate_risk(assets)
    return {
        'total_value': total_value,
        'risk_score': risk_score,
        'recommendations': generate_recommendations(risk_score)
    }

# AI suggestions will appear here`}</pre>
          </div>
          <div className="mt-3 flex space-x-2">
            <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm">
              Run Analysis
            </button>
            <button className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm">
              Clear
            </button>
          </div>
        </div>

        {/* Issue Timeline */}
        <div className="border border-gray-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Issue Timeline</h3>
          <div className="space-y-3">
            {[
              { severity: 'Critical', desc: 'Memory leak in agent loop', time: '2 min ago' },
              { severity: 'Warning', desc: 'Unoptimized database query', time: '15 min ago' },
              { severity: 'Info', desc: 'Code style violation', time: '1 hour ago' }
            ].map((issue, idx) => (
              <div key={idx} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-md">
                <div className={`w-3 h-3 rounded-full mt-1.5 ${
                  issue.severity === 'Critical' ? 'bg-red-500' :
                  issue.severity === 'Warning' ? 'bg-yellow-500' : 'bg-blue-500'
                }`}></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{issue.severity}: {issue.desc}</p>
                  <p className="text-xs text-gray-500">{issue.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Optimization Diff */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Optimization Diff</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Current Code</p>
              <div className="h-32 border border-gray-300 rounded-md bg-gray-50 p-2 font-mono text-xs text-gray-600 overflow-auto">
                <pre>{`for item in items:
    result.append(process(item))`}</pre>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Suggested Optimization</p>
              <div className="h-32 border border-green-300 rounded-md bg-green-50 p-2 font-mono text-xs text-green-800 overflow-auto">
                <pre>{`result = [process(item) for item in items]`}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIDev;
