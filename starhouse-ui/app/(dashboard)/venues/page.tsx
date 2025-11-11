import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Building } from 'lucide-react'

export default function VenuesPage() {
  return (
    <div className="container mx-auto p-8">
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold">Rental Venues</h1>
        <p className="text-muted-foreground">Manage venue rentals and bookings</p>
      </div>

      <Card className="border-2 border-dashed">
        <CardHeader>
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
            <Building className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-center">Coming Soon</CardTitle>
          <CardDescription className="text-center">
            This module is under development
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center text-sm text-muted-foreground">
          <p>Venue rental features will include:</p>
          <ul className="mt-4 space-y-2 text-left">
            <li>• Venue availability calendar</li>
            <li>• Booking management</li>
            <li>• Rental agreements and contracts</li>
            <li>• Payment tracking</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
