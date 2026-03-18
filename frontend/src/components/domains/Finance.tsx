import React from 'react';

const Finance: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Finance & Wealth Management</h2>
        <p className="text-gray-600 mb-6">
          Intelligent financial planning, investment strategies, and portfolio management.
        </p>
        
        {/* HITL Command Center */}
        <div className="border border-gray-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">HITL Command Center</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <div>
                <p className="text-sm font-medium text-gray-900">Pending Approval: Large Transaction</p>
                <p className="text-xs text-gray-500">$50,000 transfer to investment account</p>
              </div>
              <div className="space-x-2">
                <button className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                  Approve
                </button>
                <button className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700">
                  Reject
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-md">
              <div>
                <p className="text-sm font-medium text-gray-900">Portfolio Rebalancing</p>
                <p className="text-xs text-gray-500">Suggested allocation adjustment</p>
              </div>
              <div className="space-x-2">
                <button className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                  Execute
                </button>
                <button className="px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700">
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Yield Heatmap */}
        <div className="border border-gray-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Yield Heatmap</h3>
          <div className="h-48 bg-gradient-to-r from-green-100 via-yellow-100 to-red-100 rounded-md flex items-center justify-center">
            <span className="text-gray-600 text-sm font-medium">
              Market opportunity visualization will appear here
            </span>
          </div>
        </div>

        {/* Scenario Sandbox */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Scenario Sandbox</h3>
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                What if I retire at 55?
              </span>
              <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                Impact of 10% market correction?
              </span>
              <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                Tax optimization strategies?
              </span>
            </div>
            <div className="h-32 border border-gray-200 rounded-md bg-gray-50 flex items-center justify-center text-gray-500">
              Ask scenario questions to see portfolio projections
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Finance;
