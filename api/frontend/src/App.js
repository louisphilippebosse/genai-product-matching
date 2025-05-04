import React from 'react';
import MatchForm from './components/MatchForm';

function App() {
    return (
        <div className="d-flex flex-column justify-content-center align-items-center vh-100 bg-light">
            <div className="text-center mb-5">
                <h1 className="display-4">Product Matching System</h1>
                <p className="text-muted">Upload a file to find the best-matched product</p>
            </div>
            <MatchForm />
        </div>
    );
}

export default App;