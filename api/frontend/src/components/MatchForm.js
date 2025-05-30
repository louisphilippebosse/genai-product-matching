import React, { useState } from 'react';

function MatchForm() {
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false); // Add loading state

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
    };

    const handleSubmit = async (event) => {
        event.preventDefault();

        if (!file) {
            alert("Please upload a file.");
            return;
        }

        const formData = new FormData();
        formData.append("external", file);

        setLoading(true); // Start loading
        setResult(null); // Clear previous results

        try {
            const response = await fetch("/api/match", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Failed to match the product.");
            }

            const result = await response.json();
            setResult(result);
        } catch (error) {
            console.error("Error:", error);
            alert("An error occurred while matching the product.");
        } finally {
            setLoading(false); // Stop loading
        }
    };

    return (
        <div className="p-4 border rounded shadow bg-white" style={{ maxWidth: '600px', width: '100%' }}>
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <input
                        type="file"
                        name="external"
                        className="form-control"
                        onChange={handleFileChange}
                        accept=".csv" // Restrict file type to CSV
                    />
                    <small className="text-muted">
                        Please upload a CSV file with only one column and a header.
                    </small>
                </div>
                <button type="submit" className="btn btn-primary w-100" disabled={loading}>
                    {loading ? "Processing..." : "Match"}
                </button>
            </form>

            {loading && (
                <div className="mt-3 text-center">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p>Processing your request, please wait...</p>
                </div>
            )}

            {result && (
                <div className="mt-4">
                    {/* Matched Products Table */}
                    <h3>Matched Products</h3>
                    <table className="table table-bordered">
                        <thead>
                            <tr>
                                <th>Uploaded Product</th>
                                <th>Matched With</th>
                            </tr>
                        </thead>
                        <tbody>
                            {result.matchedProducts.map((product, index) => (
                                <tr key={`matched-${index}`}>
                                    <td>{product.uploaded}</td>
                                    <td>{product.matchedWith.long_name}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {/* Uncertain Matches Table */}
                    <h3>Uncertain Matches</h3>
                    <table className="table table-bordered">
                        <thead>
                            <tr>
                                <th>Uploaded Product</th>
                                <th>Possible Matches</th>
                            </tr>
                        </thead>
                        <tbody>
                            {result.uncertainMatches.map((product, index) => (
                                <tr key={`uncertain-${index}`}>
                                    <td>{product.uploaded}</td>
                                    <td>
                                        {product.possibleMatches.map((match, matchIndex) => (
                                            <span key={matchIndex}>
                                                {match.long_name}
                                                <br />
                                            </span>
                                        ))}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {/* No Matches Table */}
                    <h3>No Matches Found</h3>
                    <table className="table table-bordered">
                        <thead>
                            <tr>
                                <th>Uploaded Product</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {result.noMatches.map((product, index) => (
                                <tr key={`no-match-${index}`}>
                                    <td>{product.uploaded}</td>
                                    <td>No Match</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default MatchForm;