'use client'

import { useSession, signOut } from 'next-auth/react'
import { useRouter, usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import {
  Home,
  Activity,
  Calendar,
  BookOpen,
  Users,
  Bot,
  User,
  Target,
  TrendingUp,
  LogOut,
  ChevronDown,
  MoreHorizontal,
  Settings,
} from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: Home },
  { href: '/dashboard/wellness', label: 'Wellness', icon: Activity },
  { href: '/dashboard/calendar', label: 'Calendar', icon: Calendar },
  { href: '/dashboard/opportunities', label: 'Opportunities', icon: Target },
  { href: '/dashboard/financials', label: 'Financials', icon: TrendingUp },
  { href: '/dashboard/resources', label: 'Resources', icon: BookOpen },
  { href: '/dashboard/providers', label: 'Providers', icon: Users },
  { href: '/dashboard/digital-twin', label: 'Digital Twin', icon: Bot },
]

/** Items shown in the mobile bottom bar (first 4 + More button) */
const MOBILE_BAR_COUNT = 4

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { data: session, status } = useSession()
  const router = useRouter()
  const pathname = usePathname()
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [moreSheetOpen, setMoreSheetOpen] = useState(false)

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login')
    }
  }, [status, router])

  const handleLogout = async () => {
    setUserMenuOpen(false)
    setMoreSheetOpen(false)
    await signOut({ redirect: false })
    router.push('/')
  }

  /**
   * Determines whether a nav item is the active route.
   * The dashboard root (/dashboard) is only active on exact match.
   * Sub-routes match if the pathname starts with the href.
   */
  const isActive = (href: string): boolean => {
    if (href === '/dashboard') {
      return pathname === '/dashboard'
    }
    return pathname.startsWith(href)
  }

  if (status === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!session) {
    return null
  }

  const mobileBarItems = navItems.slice(0, MOBILE_BAR_COUNT)
  const moreMenuItems = navItems.slice(MOBILE_BAR_COUNT)

  /** Check if any item in the "More" overflow is currently active */
  const moreIsActive = moreMenuItems.some((item) => isActive(item.href))

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Top Navigation */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link href="/dashboard" className="text-xl font-bold gradient-text">
                IHEP
              </Link>
              <nav className="hidden md:flex space-x-1">
                {navItems.map((item) => {
                  const active = isActive(item.href)
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                        active
                          ? 'bg-primary/10 text-primary font-semibold'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                      aria-current={active ? 'page' : undefined}
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </nav>
            </div>
            <div className="flex items-center space-x-4 relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                aria-label="User menu"
                aria-expanded={userMenuOpen}
              >
                <span className="text-sm text-gray-600 hidden sm:inline">
                  {(() => {
                    const user: any = session.user
                    const fullName = [user?.firstName, user?.lastName].filter(Boolean).join(' ').trim()
                    return fullName || user?.username || user?.email
                  })()}
                </span>
                <User className="h-5 w-5" />
                <ChevronDown className="h-4 w-4" />
              </button>

              {/* User Dropdown Menu */}
              {userMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setUserMenuOpen(false)}
                  />
                  <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                    <Link
                      href="/dashboard"
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <Home className="h-4 w-4 mr-3" />
                      Dashboard
                    </Link>
                    <Link
                      href="/dashboard/wellness"
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <Activity className="h-4 w-4 mr-3" />
                      My Wellness
                    </Link>
                    <hr className="my-2" />
                    <button
                      onClick={handleLogout}
                      className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                    >
                      <LogOut className="h-4 w-4 mr-3" />
                      Sign Out
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content -- bottom padding accounts for mobile nav bar height */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24 md:pb-8">
        {children}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-md border-t border-gray-200 z-50"
        aria-label="Mobile navigation"
      >
        <div className="flex justify-around items-center h-16 px-1">
          {mobileBarItems.map((item) => {
            const active = isActive(item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center min-w-[56px] min-h-[48px] px-2 py-1 rounded-lg transition-colors ${
                  active
                    ? 'text-primary'
                    : 'text-gray-500'
                }`}
                aria-label={item.label}
                aria-current={active ? 'page' : undefined}
              >
                <item.icon
                  className={`h-5 w-5 ${active ? 'stroke-[2.5]' : ''}`}
                  aria-hidden="true"
                />
                <span
                  className={`text-[10px] mt-0.5 leading-tight ${
                    active ? 'font-semibold' : 'font-normal'
                  }`}
                >
                  {item.label}
                </span>
              </Link>
            )
          })}

          {/* More button -- opens the overflow sheet */}
          <button
            onClick={() => setMoreSheetOpen(true)}
            className={`flex flex-col items-center justify-center min-w-[56px] min-h-[48px] px-2 py-1 rounded-lg transition-colors ${
              moreIsActive
                ? 'text-primary'
                : 'text-gray-500'
            }`}
            aria-label="More navigation options"
            aria-expanded={moreSheetOpen}
          >
            <MoreHorizontal
              className={`h-5 w-5 ${moreIsActive ? 'stroke-[2.5]' : ''}`}
              aria-hidden="true"
            />
            <span
              className={`text-[10px] mt-0.5 leading-tight ${
                moreIsActive ? 'font-semibold' : 'font-normal'
              }`}
            >
              More
            </span>
          </button>
        </div>
      </nav>

      {/* More Menu Sheet (slides up from bottom on mobile) */}
      <Sheet open={moreSheetOpen} onOpenChange={setMoreSheetOpen}>
        <SheetContent side="bottom" className="rounded-t-2xl pb-8 max-h-[85vh] overflow-y-auto">
          <SheetHeader className="pb-2">
            <SheetTitle className="text-lg font-semibold text-gray-900">Navigation</SheetTitle>
            <SheetDescription className="sr-only">
              Additional navigation links and account options
            </SheetDescription>
          </SheetHeader>

          {/* Overflow nav items */}
          <div className="space-y-1 mt-2">
            {moreMenuItems.map((item) => {
              const active = isActive(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMoreSheetOpen(false)}
                  className={`flex items-center space-x-3 min-h-[48px] px-4 py-3 rounded-lg transition-colors ${
                    active
                      ? 'bg-primary/10 text-primary font-semibold'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                  aria-current={active ? 'page' : undefined}
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                  <span className="text-base">{item.label}</span>
                </Link>
              )
            })}
          </div>

          {/* Divider */}
          <hr className="my-4 border-gray-200" />

          {/* User / Account section */}
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 mb-2">
            Account
          </p>
          <div className="space-y-1">
            <Link
              href="/dashboard/wellness"
              onClick={() => setMoreSheetOpen(false)}
              className={`flex items-center space-x-3 min-h-[48px] px-4 py-3 rounded-lg transition-colors ${
                isActive('/dashboard/wellness')
                  ? 'bg-primary/10 text-primary font-semibold'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <User className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
              <span className="text-base">My Profile</span>
            </Link>
            <Link
              href="/dashboard"
              onClick={() => setMoreSheetOpen(false)}
              className="flex items-center space-x-3 min-h-[48px] px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
            >
              <Settings className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
              <span className="text-base">Settings</span>
            </Link>
            <button
              onClick={handleLogout}
              className="flex items-center space-x-3 min-h-[48px] px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 transition-colors w-full text-left"
            >
              <LogOut className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
              <span className="text-base">Sign Out</span>
            </button>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}
