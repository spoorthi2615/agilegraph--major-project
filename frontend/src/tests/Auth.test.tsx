// @ts-nocheck
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import LoginPage from '../components/auth/LoginPage';
import RegisterPage from '../components/auth/RegisterPage';
import ProtectedRoute from '../components/ProtectedRoute';
import Layout from '../components/Layout';
import { AuthProvider } from '../context/AuthContext';
import { apiClient } from '../api/client';

vi.mock('../api/client', () => ({
  apiClient: {
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
    logout: vi.fn(),
  }
}));

describe('Authentication & Authorization UI Tests', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    localStorage.clear();
  });

  it('renders login form and shows validation error on empty fields', async () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/Sign in to your account/i)).toBeInTheDocument();
    const submitBtn = screen.getByRole('button', { name: /Sign In/i });
    fireEvent.submit(submitBtn.closest('form')!);

    expect(await screen.findByText(/Please provide both username and password/i)).toBeInTheDocument();
  });

  it('handles successful login and token storage', async () => {
    vi.mocked(apiClient.login).mockResolvedValue({
      access_token: 'fake-jwt-token-12345',
      token_type: 'bearer',
      user: {
        username: 'alice_researcher',
        email: 'alice@example.com',
        role: 'researcher'
      }
    });

    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    fireEvent.change(screen.getByPlaceholderText(/security_lead or user@org\.com/i), {
      target: { value: 'alice_researcher' }
    });
    fireEvent.change(screen.getByPlaceholderText(/••••••••/i), {
      target: { value: 'SecurePass123!' }
    });

    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

    await waitFor(() => {
      expect(apiClient.login).toHaveBeenCalledWith({
        username: 'alice_researcher',
        password: 'SecurePass123!'
      });
      expect(localStorage.getItem('agilegraph_token')).toBe('fake-jwt-token-12345');
      expect(JSON.parse(localStorage.getItem('agilegraph_user') || '{}').username).toBe('alice_researcher');
    });
  });

  it('displays API error message on login failure', async () => {
    vi.mocked(apiClient.login).mockRejectedValue(new Error('Invalid username or password'));

    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    fireEvent.change(screen.getByPlaceholderText(/security_lead or user@org\.com/i), {
      target: { value: 'unknown_user' }
    });
    fireEvent.change(screen.getByPlaceholderText(/••••••••/i), {
      target: { value: 'wrongpassword' }
    });

    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

    expect(await screen.findByText(/Invalid username or password/i)).toBeInTheDocument();
  });

  it('validates registration form password matching and minimum length', async () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <RegisterPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/Create an AgileGraph account/i)).toBeInTheDocument();

    // Mismatched passwords
    fireEvent.change(screen.getByPlaceholderText(/e\.g\. security_lead/i), {
      target: { value: 'bob_researcher' }
    });
    fireEvent.change(screen.getByPlaceholderText(/name@organization\.com/i), {
      target: { value: 'bob@example.edu' }
    });
    fireEvent.change(screen.getByPlaceholderText(/Min\. 6 characters/i), {
      target: { value: 'passwordA' }
    });
    fireEvent.change(screen.getByPlaceholderText(/Re-enter password/i), {
      target: { value: 'passwordB' }
    });

    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    expect(await screen.findByText(/Passwords do not match/i)).toBeInTheDocument();

    // Short password
    fireEvent.change(screen.getByPlaceholderText(/Min\. 6 characters/i), {
      target: { value: '123' }
    });
    fireEvent.change(screen.getByPlaceholderText(/Re-enter password/i), {
      target: { value: '123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));
    expect(await screen.findByText(/Password must be at least 6 characters long/i)).toBeInTheDocument();
  });

  it('handles registration success with API call and token persistence', async () => {
    vi.mocked(apiClient.register).mockResolvedValue({
      access_token: 'new-user-token',
      token_type: 'bearer',
      user: {
        username: 'new_user',
        email: 'new@example.com',
        role: 'researcher'
      }
    });

    render(
      <AuthProvider>
        <BrowserRouter>
          <RegisterPage />
        </BrowserRouter>
      </AuthProvider>
    );

    fireEvent.change(screen.getByPlaceholderText(/e\.g\. security_lead/i), {
      target: { value: 'new_user' }
    });
    fireEvent.change(screen.getByPlaceholderText(/name@organization\.com/i), {
      target: { value: 'new@example.com' }
    });
    fireEvent.change(screen.getByPlaceholderText(/Min\. 6 characters/i), {
      target: { value: 'validPassword123' }
    });
    fireEvent.change(screen.getByPlaceholderText(/Re-enter password/i), {
      target: { value: 'validPassword123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }));

    await waitFor(() => {
      expect(apiClient.register).toHaveBeenCalledWith({
        username: 'new_user',
        email: 'new@example.com',
        password: 'validPassword123'
      });
      expect(localStorage.getItem('agilegraph_token')).toBe('new-user-token');
    });
  });

  it('protects routes and renders content when authenticated', async () => {
    localStorage.setItem('agilegraph_token', 'active-token');
    localStorage.setItem(
      'agilegraph_user',
      JSON.stringify({ username: 'bob', email: 'bob@example.com', role: 'researcher' })
    );
    vi.mocked(apiClient.getMe).mockResolvedValue({
      username: 'bob',
      email: 'bob@example.com',
      role: 'researcher'
    });

    render(
      <AuthProvider>
        <BrowserRouter>
          <ProtectedRoute>
            <div>Confidential Crypto Assets</div>
          </ProtectedRoute>
        </BrowserRouter>
      </AuthProvider>
    );

    expect(await screen.findByText(/Confidential Crypto Assets/i)).toBeInTheDocument();
  });

  it('displays user badge in Layout and handles sign out', async () => {
    localStorage.setItem('agilegraph_token', 'active-token');
    localStorage.setItem(
      'agilegraph_user',
      JSON.stringify({ username: 'catherine', email: 'catherine@example.com', role: 'researcher' })
    );
    vi.mocked(apiClient.getMe).mockResolvedValue({
      username: 'catherine',
      email: 'catherine@example.com',
      role: 'researcher'
    });
    vi.mocked(apiClient.logout).mockResolvedValue({ success: true });

    render(
      <AuthProvider>
        <BrowserRouter>
          <Layout>
            <div>Protected Content</div>
          </Layout>
        </BrowserRouter>
      </AuthProvider>
    );

    expect(await screen.findByText('catherine')).toBeInTheDocument();
    const signOutBtn = screen.getByRole('button', { name: /Sign Out/i });
    fireEvent.click(signOutBtn);

    await waitFor(() => {
      expect(apiClient.logout).toHaveBeenCalled();
      expect(localStorage.getItem('agilegraph_token')).toBeNull();
      expect(localStorage.getItem('agilegraph_user')).toBeNull();
    });
  });
});
