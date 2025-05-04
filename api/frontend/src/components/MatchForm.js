import React, { useState } from 'react';

function MatchForm() {
    const [file, setFile] = useState(null);
    const [matchedProduct, setMatchedProduct] = useState(null);

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
            setMatchedProduct(result.matchedProduct);
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
            {matchedProduct && (
                <div className="mt-4">
                    <h3>Matched Product:</h3>
                    <p>{matchedProduct}</p>
                </div>
            )}
        </div>
    );
}

export default MatchForm;