import React from 'react';
import { NavLink } from 'react-router-dom';
import { Button } from '@chakra-ui/react';

const BaseLayout: React.FC = ({ children }) => (
  <div className="min-h-screen bg-gray-100">
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <img
                className="h-8 w-auto"
                src="/vite.svg"
                alt="Vite"
              />
            </div>
            <div className="ml-10">
              <h1 className="text-xl font-bold text-gray-900">Dr. Ikechukwu PA</h1>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="ml-10">
              <NavLink to="/" className="px-3 py-2 rounded-md text-sm font-medium text-gray-900 hover:text-gray-900">Home</NavLink>
              <NavLink to="/clinical" className="px-3 py-2 rounded-md text-sm font-medium text-gray-900 hover:text-gray-900">Clinical</NavLink>
              <NavLink to="/finance" className="px-3 py-2 rounded-md text-sm font-medium text-gray-900 hover:text-gray-900">Finance</NavLink>
              <NavLink to="/ai-dev" className="px-3 py-2 rounded-md text-sm font-medium text-gray-900 hover:text-gray-900">AI Dev</NavLink>
              <NavLink to="/fashion" className="px-3 py-2 rounded-md text-sm font-medium text-gray-900 hover:text-gray-900">Fashion</NavLink>
            </div>
          </div>
        </div>
      </div>
    </header>
    <main className="max-w-7xl mx-auto px-4 sm:px-6">
      <div className="py-12">
        {children}
      </div>
    </main>
    <footer className="bg-white shadow-sm mt-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <p className="text-center text-gray-500">© {new Date().getFullYear()} Dr. Ikechukwu PA</p>
      </div>
    </footer>
  </div>
);

export default BaseLayout