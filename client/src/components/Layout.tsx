import { Outlet } from 'react-router-dom'
import { useTelegramBackButton } from '../hooks/useTelegramBackButton'
import { useStartParamRedirect } from '../hooks/useStartParamRedirect'

export default function Layout() {
  useTelegramBackButton()
  useStartParamRedirect()

  return (
    <div className="min-h-screen bg-bg-primary">
      <main>
        <Outlet />
      </main>
    </div>
  )
}
