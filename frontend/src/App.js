import React from 'react';
import AudioUploader from './AudioUploader';
import NoteDisplay from './NoteDisplay';

function App() {
    return (
        <div>
            <h1>Medical Note Generator</h1>
            <AudioUploader />
            <NoteDisplay />
        </div>
    );
}

export default App;