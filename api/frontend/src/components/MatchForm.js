import React, { useState } from 'react';

function MatchForm() {
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);

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
                    />
                </div>
                <button type="submit" className="btn btn-primary w-100">
                    Match
                </button>
            </form>
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
                                    <td>{product.matchedWith}</td>
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
                                                {match}
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