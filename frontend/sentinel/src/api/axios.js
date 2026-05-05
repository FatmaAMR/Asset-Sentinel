import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8002/api/v1/reports',
  headers: {
    'Content-Type': 'application/json',
  }
});

export default client;