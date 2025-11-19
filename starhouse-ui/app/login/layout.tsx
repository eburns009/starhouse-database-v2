import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Login',
  description: 'Sign in to your StarHouse CRM account to manage contacts, donors, and membership.',
  robots: 'noindex, nofollow', // Don't index login pages
}

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
