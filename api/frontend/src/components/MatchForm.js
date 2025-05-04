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
        <div className="p-4 border rounded shadow bg-white" style={{ maxWidth: '400px', width: '100%' }}>
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
                    {result.matchedProducts.length > 0 && (
                        <>
                            <h3>Matched Products:</h3>
                            <ul>
                                {result.matchedProducts.map((product, index) => (
                                    <li key={index}>
                                        Uploaded: {product.uploaded}, Matched With: {product.matchedWith}
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}
                    {result.uncertainMatches.length > 0 && (
                        <>
                            <h3>Uncertain Matches:</h3>
                            <ul>
                                {result.uncertainMatches.map((product, index) => (
                                    <li key={index}>
                                        Uploaded: {product.uploaded}
                                        <ul>
                                            {product.possibleMatches.map((match, matchIndex) => (
                                                <li key={matchIndex}>Possible Match: {match}</li>
                                            ))}
                                        </ul>
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}
                    {result.noMatches.length > 0 && (
                        <>
                            <h3>No Matches Found:</h3>
                            <ul>
                                {result.noMatches.map((product, index) => (
                                    <li key={index}>
                                        Uploaded: {product.uploaded}
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}
                </div>
            )}
        </div>
    );
}

export default MatchForm;