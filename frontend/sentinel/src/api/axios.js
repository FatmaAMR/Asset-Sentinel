import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8004/api/v1/reports',
  headers: {
    'Content-Type': 'application/json',
  }
});

export default client;