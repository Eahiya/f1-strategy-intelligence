import React, { Component } from 'react';
import { AlertCircle, RefreshCcw } from 'lucide-react';

/**
 * Error Boundary - Production Error Handling
 * 
 * Catches JavaScript errors anywhere in child component tree,
 * logs errors, and displays fallback UI instead of crashing.
 */

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so next render shows fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('ErrorBoundary caught error:', error);
    console.error('Component stack:', errorInfo.componentStack);
    
    this.setState({
      error,
      errorInfo
    });

    // Send to error reporting service in production
    if (process.env.NODE_ENV === 'production' && window.errorReporter) {
      window.errorReporter.report(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null,
      errorInfo: null 
    });
    
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { error } = this.state;
      const errorMessage = error?.message || 'An unexpected error occurred';
      
      return (
        <div className="min-h-screen bg-black flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-gradient-to-br from-gray-900 to-black border border-red-900/50 rounded-xl p-8">
            <div className="flex items-center justify-center mb-6">
              <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
            </div>
            
            <h2 className="text-xl font-bold text-white text-center mb-2">
              System Error
            </h2>
            
            <p className="text-gray-400 text-center mb-6 text-sm">
              {errorMessage}
            </p>
            
            {process.env.NODE_ENV === 'development' && (
              <div className="mb-6 p-4 bg-black/50 rounded-lg overflow-auto max-h-48">
                <pre className="text-xs text-red-400 font-mono">
                  {error?.stack}
                </pre>
              </div>
            )}
            
            <div className="flex gap-3">
              <button
                onClick={this.handleRetry}
                className="flex-1 flex items-center justify-center gap-2 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
              >
                <RefreshCcw className="w-4 h-4" />
                Retry
              </button>
              
              <button
                onClick={this.handleReload}
                className="flex-1 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
              >
                Reload Page
              </button>
            </div>
            
            <p className="text-xs text-gray-600 text-center mt-4">
              F1 Strategy Platform v6.3
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
