/**
 * Signup Page
 * 
 * Why this exists:
 * - Allows new users to create an account
 * - Validates password confirmation
 * - Automatically logs in after successful signup
 * 
 * Features:
 * - Password confirmation validation
 * - Email format validation (optional field)
 * - Error handling and display
 * - Auto-login on success
 */

import { useState } from 'react'
import type { FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

interface SignupResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  role: 'card_user' | 'operator';
}

export default function Signup() {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  // Form state
  const [userId, setUserId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  /**
   * Validate form inputs.
   * 
   * Checks:
   * - user_id is not empty
   * - password is at least 8 characters
   * - password confirmation matches
   * - email format if provided
   */
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!userId.trim()) {
      newErrors.userId = 'User ID is required';
    }
    
    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    if (email && !email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      newErrors.email = 'Invalid email format';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission.
   * 
   * Steps:
   * 1. Validate form
   * 2. Call POST /auth/signup
   * 3. Auto-login with returned token
   * 4. Redirect to dashboard
   */
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          email_masked: email || undefined,
          password,
          password_confirm: confirmPassword,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Signup failed' }));
        throw new Error(errorData.detail || 'Failed to create account');
      }
      
      const data: SignupResponse = await response.json();
      
      // Auto-login with returned token
      login(data.access_token);
      
      toast.success('Account created!', {
        description: `Welcome to SpendSense, ${data.user_id}!`,
      });
      
      // Redirect to dashboard (new users are always card_user role)
      navigate('/dashboard');
      
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Signup failed';
      toast.error('Signup failed', { description: message });
      setErrors({ submit: message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      {/* Left side - Gradient illustration/pattern */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-purple-600 via-pink-600 to-blue-600 p-12 flex-col justify-between relative overflow-hidden rounded-r-3xl shadow-2xl">
        {/* Decorative circles */}
        <div className="absolute top-20 left-20 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-white/10 rounded-full blur-3xl" />
        
        {/* Content */}
        <div className="relative z-10">
          <h1 className="text-4xl font-bold text-white mb-4">
            Join SpendSense
          </h1>
          <p className="text-white/90 text-lg leading-relaxed">
            Start your journey to better financial insights. Get personalized recommendations
            based on your unique behavioral patterns.
          </p>
        </div>
        
        {/* Benefits list */}
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-3 text-white">
            <div className="rounded-lg bg-white/20 p-2 backdrop-blur-sm">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span>Free to use, no credit card required</span>
          </div>
          <div className="flex items-center gap-3 text-white">
            <div className="rounded-lg bg-white/20 p-2 backdrop-blur-sm">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span>Secure and private data handling</span>
          </div>
          <div className="flex items-center gap-3 text-white">
            <div className="rounded-lg bg-white/20 p-2 backdrop-blur-sm">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span>Get started in under 2 minutes</span>
          </div>
        </div>
      </div>
      
      {/* Right side - Signup form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 overflow-y-auto">
        <div className="w-full max-w-md space-y-8">
          {/* Mobile gradient header */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-block rounded-xl bg-gradient-to-br from-purple-600 via-pink-600 to-blue-600 p-3 mb-4">
              <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-foreground">Join SpendSense</h2>
          </div>
          
          <Card className="border-2 shadow-xl">
            <CardHeader className="space-y-1">
              <CardTitle className="text-2xl font-bold">
                Create Account
              </CardTitle>
              <CardDescription>
                Sign up for SpendSense to get started
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* General error message */}
                {errors.submit && (
                  <div className="flex items-start gap-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
                    <svg className="h-5 w-5 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{errors.submit}</span>
                  </div>
                )}
                
                {/* User ID field */}
                <div className="space-y-2">
                  <label htmlFor="userId" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    User ID <span className="text-red-500">*</span>
                  </label>
                  <Input
                    id="userId"
                    type="text"
                    placeholder="e.g., usr_123456"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                    disabled={isLoading}
                    required
                    className="h-11"
                  />
                  {errors.userId && (
                    <p className="text-xs text-red-600 dark:text-red-400">{errors.userId}</p>
                  )}
                </div>
                
                {/* Email field (optional) */}
                <div className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    Email (optional)
                  </label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                    className="h-11"
                  />
                  {errors.email && (
                    <p className="text-xs text-red-600 dark:text-red-400">{errors.email}</p>
                  )}
                </div>
                
                {/* Password field */}
                <div className="space-y-2">
                  <label htmlFor="password" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    Password <span className="text-red-500">*</span>
                  </label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="At least 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoading}
                    required
                    className="h-11"
                  />
                  {errors.password && (
                    <p className="text-xs text-red-600 dark:text-red-400">{errors.password}</p>
                  )}
                </div>
                
                {/* Confirm password field */}
                <div className="space-y-2">
                  <label htmlFor="confirmPassword" className="text-sm font-medium text-foreground flex items-center gap-2">
                    <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Confirm Password <span className="text-red-500">*</span>
                  </label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Re-enter your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    disabled={isLoading}
                    required
                    className="h-11"
                  />
                  {errors.confirmPassword && (
                    <p className="text-xs text-red-600 dark:text-red-400">{errors.confirmPassword}</p>
                  )}
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
                      Creating account...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                      </svg>
                      Sign Up
                    </span>
                  )}
                </Button>
                
                {/* Link to login */}
                <div className="text-center text-sm text-muted-foreground pt-2">
                  Already have an account?{' '}
                  <Link to="/login" className="text-primary hover:underline font-medium">
                    Log in
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

