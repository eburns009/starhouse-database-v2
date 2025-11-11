import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Sparkles } from 'lucide-react'

export default function OfferingsPage() {
  return (
    <div className="container mx-auto p-8">
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold">StarHouse Offerings</h1>
        <p className="text-muted-foreground">Manage courses, events, and programs</p>
      </div>

      <Card className="border-2 border-dashed">
        <CardHeader>
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-center">Coming Soon</CardTitle>
          <CardDescription className="text-center">
            This module is under development
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center text-sm text-muted-foreground">
          <p>Offerings management features will include:</p>
          <ul className="mt-4 space-y-2 text-left">
            <li>• Course and event catalog</li>
            <li>• Registration management</li>
            <li>• Participant tracking</li>
            <li>• Feedback and reviews</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
