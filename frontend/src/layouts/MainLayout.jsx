import { useState } from "react"
import { Outlet } from "react-router-dom"
import { Sidebar, MobileSidebar } from "./Sidebar"
import { Header } from "./Header"
import { SidebarProvider } from "@/context/SidebarContext"
import { TooltipProvider } from "@/components/ui/tooltip"
import PushSubscriptionManager from "@/features/notifications/components/PushSubscriptionManager"

function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <SidebarProvider>
      <TooltipProvider>
        <PushSubscriptionManager />
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
      </TooltipProvider>
    </SidebarProvider>
  )
}

export default MainLayout
