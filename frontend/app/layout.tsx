import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/lib/auth-context'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'a6hub - Collaborative Chip Design Platform',
  description: 'Cloud-based platform for collaborative ASIC chip design automation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: '#000',
                color: '#fff',
                border: '1px solid #fff',
              },
              success: {
                iconTheme: {
                  primary: '#fff',
                  secondary: '#000',
                },
              },
              error: {
                iconTheme: {
                  primary: '#fff',
                  secondary: '#000',
                },
              },
            }}
          />
        </AuthProvider>
      </body>
    </html>
  )
}
