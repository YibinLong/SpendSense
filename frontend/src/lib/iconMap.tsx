/**
 * Icon Mapping Utilities
 * 
 * Why this file exists:
 * - Centralizes icon selection logic for consistency
 * - Maps persona types, signal types, and status types to appropriate lucide-react icons
 * - Makes it easy to get the right icon based on data type
 * 
 * Usage:
 * - Import the get*Icon functions and render the returned component
 * - All icons come from lucide-react for consistency
 */

import {
  Shield,
  TrendingDown,
  List,
  PiggyBank,
  Zap,
  AlertCircle,
  // Signal type icons
  Repeat,
  DollarSign,
  CreditCard,
  TrendingUp,
  // Status icons
  CheckCircle,
  XCircle,
  Flag,
  Clock,
  Eye,
  // Action icons
  LogOut,
  Home,
  LayoutDashboard,
  Users,
  // Item type icons
  BookOpen,
  Gift,
  // Auth icons
  Mail,
  Lock,
  LogIn,
  UserPlus,
  // Empty state icons
  Inbox,
  Search,
  // Chart icons
  BarChart3,
  LineChart,
  PieChart,
  Activity,
  // Other utility icons
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  X,
  Check,
  Info,
  AlertTriangle,
  HelpCircle,
} from 'lucide-react';

import type { LucideProps } from 'lucide-react';
import type { FC } from 'react';

// Type for Lucide icon components
type LucideIcon = FC<LucideProps>;

/**
 * Get icon for a persona type.
 * 
 * Why: Each persona has a unique visual identity. Icons help users
 * quickly recognize and understand different persona types.
 * 
 * @param personaId - The persona identifier (e.g., 'high_utilization')
 * @returns Lucide icon component
 */
export function getPersonaIcon(personaId: string): LucideIcon {
  const iconMap: Record<string, LucideIcon> = {
    'high_utilization': Shield,           // Shield for protection/concern
    'variable_income_budgeter': TrendingDown, // Trending down for variable income
    'subscription_heavy': List,           // List for multiple subscriptions
    'savings_builder': PiggyBank,         // Piggy bank for savings
    'cash_flow_optimizer': Zap,           // Lightning for optimization/efficiency
    'insufficient_data': AlertCircle,     // Alert for insufficient data
  };

  return iconMap[personaId] || AlertCircle;
}

/**
 * Get icon for a signal type.
 * 
 * Why: Signals represent different aspects of financial behavior.
 * Icons make it easier to scan and identify signal categories.
 * 
 * @param signalType - The signal type (subscriptions, savings, credit, income)
 * @returns Lucide icon component
 */
export function getSignalIcon(signalType: string): LucideIcon {
  const iconMap: Record<string, LucideIcon> = {
    'subscriptions': Repeat,     // Repeat for recurring payments
    'savings': PiggyBank,         // Piggy bank for savings
    'credit': CreditCard,         // Credit card for credit signals
    'income': DollarSign,         // Dollar sign for income
  };

  return iconMap[signalType] || Activity;
}

/**
 * Get icon for a recommendation item type.
 * 
 * Why: Differentiates educational content from partner offers visually.
 * 
 * @param itemType - The item type (education, offer)
 * @returns Lucide icon component
 */
export function getItemTypeIcon(itemType: string): LucideIcon {
  const iconMap: Record<string, LucideIcon> = {
    'education': BookOpen,   // Book for educational content
    'offer': Gift,           // Gift for partner offers
  };

  return iconMap[itemType] || Info;
}

/**
 * Get icon for a status type.
 * 
 * Why: Status indicators need clear visual cues. Icons combined with
 * colors make status immediately recognizable.
 * 
 * @param status - The status (approved, rejected, flagged, pending)
 * @returns Lucide icon component
 */
export function getStatusIcon(status: string): LucideIcon {
  const iconMap: Record<string, LucideIcon> = {
    'approved': CheckCircle,   // Check for approved
    'rejected': XCircle,       // X for rejected
    'flagged': Flag,           // Flag for flagged items
    'pending': Clock,          // Clock for pending
  };

  return iconMap[status] || Clock;
}

/**
 * Get icon for navigation items.
 * 
 * Why: Navigation is clearer with icons. This provides consistent
 * icons for common navigation destinations.
 * 
 * @param navItem - The navigation item identifier
 * @returns Lucide icon component
 */
export function getNavIcon(navItem: string): LucideIcon {
  const iconMap: Record<string, LucideIcon> = {
    'home': Home,
    'dashboard': LayoutDashboard,
    'operator': Users,
    'logout': LogOut,
    'profile': Eye,
  };

  return iconMap[navItem] || Home;
}

/**
 * Get icon for chart types.
 * 
 * Why: Helps users identify different chart types at a glance.
 * 
 * @param chartType - The chart type identifier
 * @returns Lucide icon component
 */
export function getChartIcon(chartType: string): LucideIcon {
  const iconMap: Record<string, LucideIcon> = {
    'bar': BarChart3,
    'line': LineChart,
    'pie': PieChart,
    'trend': TrendingUp,
    'activity': Activity,
  };

  return iconMap[chartType] || BarChart3;
}

/**
 * Export commonly used icons for direct import.
 * 
 * Why: Makes it convenient to import frequently used icons without
 * going through the mapping functions.
 */
export const CommonIcons = {
  // Auth
  Mail,
  Lock,
  LogIn,
  LogOut,
  UserPlus,
  
  // Navigation
  Home,
  LayoutDashboard,
  Users,
  Eye,
  
  // Actions
  CheckCircle,
  XCircle,
  Flag,
  Clock,
  
  // Content
  BookOpen,
  Gift,
  Info,
  AlertCircle,
  AlertTriangle,
  HelpCircle,
  
  // Chevrons
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  
  // Utility
  X,
  Check,
  Search,
  Inbox,
  
  // Charts
  BarChart3,
  LineChart,
  PieChart,
  Activity,
  TrendingUp,
};

