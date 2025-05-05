import React from 'react';
import MatchForm from './components/MatchForm';

function App() {
    return (
        <div className="d-flex flex-column vh-100 bg-light overflow-auto">
            <div className="text-center mb-4 p-3">
                <h1 className="display-4">Product Matching System</h1>
                <p className="text-muted">Upload a file to find the best-matched product</p>
            </div>
            <div className="flex-grow-1 d-flex justify-content-center align-items-start">
                <MatchForm />
            </div>
        </div>
    );
}

export default App;