import { Card, CardContent, CardHeader } from "@/components/ui/card"

export function CapabilityMapPage() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <h2 className="text-2xl font-semibold">Capability Map</h2>
          <p className="text-muted-foreground">
            View and manage your business capabilities
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex min-h-[400px] flex-col items-center justify-center">
            <h3 className="text-lg font-medium">Business Capability Management</h3>
            <p className="mt-2 text-sm text-muted-foreground text-center">
              Visualize and manage your organization's business capabilities.<br />
              Create, edit, and organize capabilities in a hierarchical structure.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 