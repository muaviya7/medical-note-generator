import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://localhost:8000',
});

export const uploadAudio = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/upload', formData);
    return response.data;
};

export const fetchGeneratedNote = async () => {
    const response = await apiClient.get('/note');
    return response.data;
};