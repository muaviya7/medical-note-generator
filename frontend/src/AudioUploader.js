import React from 'react';

function AudioUploader() {
    const handleUpload = (event) => {
        const file = event.target.files[0];
        console.log("Uploaded file:", file);
    };

    return (
        <div>
            <h2>Upload Audio</h2>
            <input type="file" accept="audio/*" onChange={handleUpload} />
        </div>
    );
}

export default AudioUploader;