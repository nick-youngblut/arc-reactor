'use client';

import type { ErrorInfo, ReactNode } from 'react';
import { Component } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Global UI error', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] items-center justify-center px-6">
          <div className="arc-surface w-full max-w-xl p-8 text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-arc-gray-400">
              Arc Reactor
            </p>
            <h1 className="mt-4 text-2xl font-semibold text-content">
              Something went wrong in the workspace
            </h1>
            <p className="mt-3 text-sm text-arc-gray-500 dark:text-arc-gray-300">
              Refresh the page or try again. If the issue persists, contact the platform team.
            </p>
            <div className="mt-6 flex items-center justify-center gap-3">
              <button
                className="rounded-full bg-arc-blue px-5 py-2 text-sm font-semibold text-white transition hover:opacity-90"
                onClick={this.handleReset}
                type="button"
              >
                Try again
              </button>
              <button
                className="rounded-full border border-arc-gray-200 px-5 py-2 text-sm font-semibold text-arc-gray-600 transition hover:bg-arc-gray-100 dark:border-arc-gray-700 dark:text-arc-gray-200 dark:hover:bg-arc-gray-800"
                onClick={() => window.location.reload()}
                type="button"
              >
                Reload
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
