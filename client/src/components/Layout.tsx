import { Outlet } from 'react-router-dom'
import { useTelegramBackButton } from '../hooks/useTelegramBackButton'

export default function Layout() {
  useTelegramBackButton()

  return (
    <div className="min-h-screen bg-telegram-bg">
      <main className="pb-safe-area-bottom">
        <Outlet />
      </main>
    </div>
  )
}


