/**
 * Login Page
 * 
 * Why this exists:
 * - Allows users and operators to authenticate with username/password
 * - Stores JWT token on successful login
 * - Redirects to appropriate dashboard based on role
 * 
 * Features:
 * - Form validation (required fields)
 * - Error handling and display
 * - Loading states during API calls
 * - Link to signup page
 */

import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  role: 'card_user' | 'operator';
}

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  // Form state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  /**
   * Handle form submission.
   * 
   * Steps:
   * 1. Validate inputs (non-empty)
   * 2. Call POST /auth/login
   * 3. Store token in localStorage via AuthContext
   * 4. Redirect to /dashboard (card_user) or /operator (operator)
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Validate inputs
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Call login endpoint
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(errorData.detail || 'Invalid credentials');
      }
      
      const data: LoginResponse = await response.json();
      
      // Store token and update auth context
      login(data.access_token);
      
      toast.success('Login successful', {
        description: `Welcome back, ${data.user_id}!`,
      });
      
      // Redirect based on role
      if (data.role === 'operator') {
        navigate('/operator');
      } else {
        navigate('/dashboard');
      }
      
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      toast.error('Login failed', { description: message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Welcome to SpendSense
          </CardTitle>
          <CardDescription className="text-center">
            Enter your credentials to access your account
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Error message display */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md text-sm">
                {error}
              </div>
            )}
            
            {/* Username field */}
            <div className="space-y-2">
              <label htmlFor="username" className="text-sm font-medium text-gray-700">
                Username
              </label>
              <Input
                id="username"
                type="text"
                placeholder="usr_000001 or operator@spendsense.local"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoading}
                required
              />
              <p className="text-xs text-gray-500">
                Try: usr_000001 or operator@spendsense.local
              </p>
            </div>
            
            {/* Password field */}
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-gray-700">
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                required
              />
              <p className="text-xs text-gray-500">
                Try: usr000001123 or operator123
              </p>
            </div>
            
            {/* Submit button */}
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Logging in...' : 'Log In'}
            </Button>
            
            {/* Link to signup */}
            <div className="text-center text-sm text-gray-600">
              Don't have an account?{' '}
              <Link to="/signup" className="text-blue-600 hover:text-blue-700 font-medium">
                Sign up
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

