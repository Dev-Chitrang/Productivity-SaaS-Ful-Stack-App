import { useState } from "react"
import { Outlet } from "react-router-dom"
import { Sidebar, MobileSidebar } from "./Sidebar"
import { Header } from "./Header"

function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen bg-background">
      <MobileSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default MainLayout
