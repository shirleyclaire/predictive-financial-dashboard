import axios from 'axios';

const API_URL = 'http://localhost/api';

export const login = async (email, password) => {
  const response = await axios.post(`${API_URL}/expenses/token`, {
    username: email,
    password: password
  });
  if (response.data.access_token) {
    localStorage.setItem('token', response.data.access_token);
  }
  return response.data;
};

export const logout = () => {
  localStorage.removeItem('token');
};

export const isAuthenticated = () => {
  return localStorage.getItem('token') !== null;
};
