import React from 'react';

const Fashion: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Fashion & Lifestyle</h2>
        <p className="text-gray-600 mb-6">
          Personalized style recommendations and fashion insights.
        </p>
        
        {/* Style Board */}
        <div className="border border-gray-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Style Board</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((item) => (
              <div key={item} className="aspect-square bg-gray-100 rounded-md flex items-center justify-center text-gray-400 border border-gray-200">
                <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            ))}
          </div>
        </div>

        {/* Domain Toggle */}
        <div className="border border-gray-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Style Focus</h3>
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-gray-700">Corporate</span>
            <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-blue-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
              <span className="inline-block h-4 w-4 transform rounded-full bg-white transition-transform translate-x-6"></span>
            </button>
            <span className="text-sm font-medium text-gray-700">Cultural</span>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Toggle between professional attire and traditional/cultural styles
          </p>
        </div>

        {/* Sourcing Drawer */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Sourcing Information</h3>
          <div className="space-y-2">
            {[
              { store: 'BellaNaija', price: '₦45,000', item: 'Ankara print dress' },
              { store: 'Jiji', price: '₦12,000', item: 'Leather tote bag' },
              { store: 'Local tailor', price: '₦25,000', item: 'Custom agbada' }
            ].map((source, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div>
                  <p className="text-sm font-medium text-gray-900">{source.item}</p>
                  <p className="text-xs text-gray-500">{source.store}</p>
                </div>
                <span className="text-sm font-semibold text-gray-700">{source.price}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Fashion;
