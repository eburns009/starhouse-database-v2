import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Toaster } from 'sonner'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: {
    default: 'StarHouse CRM - Contact & Membership Management',
    template: '%s | StarHouse CRM' // Page-specific titles will use this template
  },
  description: 'Professional contact and membership management system for StarHouse. Manage donors, members, venues, and offerings all in one place.',
  keywords: ['CRM', 'contact management', 'membership', 'donor management', 'StarHouse'],
  authors: [{ name: 'StarHouse' }],
  creator: 'StarHouse',
  publisher: 'StarHouse',

  // Open Graph metadata for social media sharing
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://starhouse-database-v2.vercel.app',
    siteName: 'StarHouse CRM',
    title: 'StarHouse CRM - Contact & Membership Management',
    description: 'Professional contact and membership management system for StarHouse',
    images: [
      {
        url: '/og-image.png', // TODO: Create this image (1200x630px)
        width: 1200,
        height: 630,
        alt: 'StarHouse CRM',
      },
    ],
  },

  // Twitter Card metadata
  twitter: {
    card: 'summary_large_image',
    title: 'StarHouse CRM - Contact & Membership Management',
    description: 'Professional contact and membership management system for StarHouse',
    images: ['/og-image.png'], // TODO: Create this image
  },

  // Robots directive
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },

  // Verification (add when you have them)
  // verification: {
  //   google: 'google-site-verification-code',
  //   yandex: 'yandex-verification-code',
  // },

  // App metadata for PWA (future enhancement)
  applicationName: 'StarHouse CRM',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'StarHouse CRM',
  },
  formatDetection: {
    telephone: false,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased">
        {children}
        <Toaster richColors position="top-right" />
      </body>
    </html>
  )
}
