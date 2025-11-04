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
    <div className="min-h-screen flex bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      {/* Left side - Gradient illustration/pattern */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 p-12 flex-col justify-between relative overflow-hidden rounded-r-3xl shadow-2xl">
        {/* Decorative circles */}
        <div className="absolute top-20 right-20 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 left-20 w-96 h-96 bg-white/10 rounded-full blur-3xl" />
        
        {/* Content */}
        <div className="relative z-10">
          <h1 className="text-4xl font-bold text-white mb-4">
            Welcome to SpendSense
          </h1>
          <p className="text-white/90 text-lg leading-relaxed">
            Transform financial data into actionable insights with personalized recommendations
            and behavioral analytics.
          </p>
        </div>
        
        {/* Features list */}
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-3 text-white">
            <div className="rounded-lg bg-white/20 p-2 backdrop-blur-sm">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <span>Behavioral persona assignment</span>
          </div>
          <div className="flex items-center gap-3 text-white">
            <div className="rounded-lg bg-white/20 p-2 backdrop-blur-sm">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <span>Personalized financial education</span>
          </div>
          <div className="flex items-center gap-3 text-white">
            <div className="rounded-lg bg-white/20 p-2 backdrop-blur-sm">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <span>Explainable recommendations</span>
          </div>
        </div>
      </div>
      
      {/* Right side - Login form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile gradient header */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-block rounded-xl bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 p-3 mb-4">
              <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-foreground">Welcome to SpendSense</h2>
          </div>
          
          <Card className="border-2 shadow-xl">
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl font-bold">
                Sign In
              </CardTitle>
              <CardDescription>
                Enter your credentials to access your account
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Error message display */}
                {error && (
                  <div className="flex items-start gap-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
                    <svg className="h-5 w-5 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{error}</span>
                  </div>
                )}
                
                {/* Username field */}
                <div className="space-y-2">
                  <label htmlFor="username" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
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
                    className="h-11"
                  />
                  <p className="text-xs text-muted-foreground">
                    Try: usr_000001 or operator@spendsense.local
                  </p>
                </div>
                
                {/* Password field */}
                <div className="space-y-2">
                  <label htmlFor="password" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
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
                    className="h-11"
                  />
                  <p className="text-xs text-muted-foreground">
                    Try: usr000001123 or operator123
                  </p>
                </div>
                
                {/* Submit button with gradient */}
                <Button
                  type="submit"
                  variant="gradient"
                  className="w-full h-11"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Logging in...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                      </svg>
                      Log In
                    </span>
                  )}
                </Button>
                
                {/* Link to signup */}
                <div className="text-center text-sm text-muted-foreground pt-2">
                  Don't have an account?{' '}
                  <Link to="/signup" className="text-primary hover:underline font-medium">
                    Sign up
                  </Link>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

