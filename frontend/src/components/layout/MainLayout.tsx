import { ReactNode } from "react"
import { Link, useLocation } from "react-router-dom"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Toaster } from "@/components/ui/sonner"
import { cn } from "@/lib/utils"

interface MainLayoutProps {
  children: ReactNode
}

const navigation = [
  { name: "Capability Map", href: "/" },
  { name: "Business Goals", href: "/goals" },
  { name: "Analysis", href: "/analysis" },
]

export function MainLayout({ children }: MainLayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center px-4">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg bg-primary"></div>
            <h1 className="text-xl font-bold">Business Capability Map</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        {/* Navigation */}
        <div className="mb-6">
          <nav className="flex space-x-1">
            {navigation.map((item) => (
              <Button
                key={item.name}
                asChild
                variant={location.pathname === item.href ? "default" : "ghost"}
                className={cn(
                  "justify-start",
                  location.pathname === item.href && "bg-primary text-primary-foreground"
                )}
              >
                <Link to={item.href}>{item.name}</Link>
              </Button>
            ))}
          </nav>
        </div>

        <Separator className="mb-6" />

        {/* Page Content */}
        <div className="space-y-4">
          {children}
        </div>
      </div>

      <Toaster />
    </div>
  )
} 