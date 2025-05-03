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
        <div>
            <form onSubmit={handleSubmit}>
                <input type="file" name="external" onChange={handleFileChange} />
                <button type="submit">Match</button>
            </form>
            {matchedProduct && (
                <div>
                    <h3>Matched Product:</h3>
                    <p>{matchedProduct}</p>
                </div>
            )}
        </div>
    );
}

export default MatchForm;