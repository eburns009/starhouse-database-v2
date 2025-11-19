import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Reset Password',
  description: 'Reset your StarHouse CRM account password securely.',
  robots: 'noindex, nofollow', // Don't index auth pages
}

export default function ResetPasswordLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
