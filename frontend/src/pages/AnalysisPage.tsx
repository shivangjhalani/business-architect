import { Card, CardContent, CardHeader } from "@/components/ui/card"

export function AnalysisPage() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <h2 className="text-2xl font-semibold">Analysis & Recommendations</h2>
          <p className="text-muted-foreground">
            AI-powered analysis of your capability map
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex min-h-[400px] flex-col items-center justify-center">
            <h3 className="text-lg font-medium">AI Analysis</h3>
            <p className="mt-2 text-sm text-muted-foreground text-center">
              Get intelligent recommendations for your business capabilities.<br />
              View and apply AI-generated suggestions.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 