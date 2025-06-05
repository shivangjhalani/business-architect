import { Card, CardContent, CardHeader } from "@/components/ui/card"

export function BusinessGoalsPage() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <h2 className="text-2xl font-semibold">Business Goals</h2>
          <p className="text-muted-foreground">
            Submit and track your business goals
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex min-h-[400px] flex-col items-center justify-center">
            <h3 className="text-lg font-medium">Business Goals Management</h3>
            <p className="mt-2 text-sm text-muted-foreground text-center">
              Submit new business goals and track their progress.<br />
              Upload PDFs and get AI-powered analysis.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 