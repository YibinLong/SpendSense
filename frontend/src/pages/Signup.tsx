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

import { useState, FormEvent } from 'react';
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Create Account
          </CardTitle>
          <CardDescription className="text-center">
            Sign up for SpendSense to get started
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* General error message */}
            {errors.submit && (
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md text-sm">
                {errors.submit}
              </div>
            )}
            
            {/* User ID field */}
            <div className="space-y-2">
              <label htmlFor="userId" className="text-sm font-medium text-gray-700">
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
              />
              {errors.userId && (
                <p className="text-xs text-red-600">{errors.userId}</p>
              )}
            </div>
            
            {/* Email field (optional) */}
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-gray-700">
                Email (optional)
              </label>
              <Input
                id="email"
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
              />
              {errors.email && (
                <p className="text-xs text-red-600">{errors.email}</p>
              )}
            </div>
            
            {/* Password field */}
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-gray-700">
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
              />
              {errors.password && (
                <p className="text-xs text-red-600">{errors.password}</p>
              )}
            </div>
            
            {/* Confirm password field */}
            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
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
              />
              {errors.confirmPassword && (
                <p className="text-xs text-red-600">{errors.confirmPassword}</p>
              )}
            </div>
            
            {/* Submit button */}
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? 'Creating account...' : 'Sign Up'}
            </Button>
            
            {/* Link to login */}
            <div className="text-center text-sm text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-600 hover:text-blue-700 font-medium">
                Log in
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

