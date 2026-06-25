import { Toaster } from "react-hot-toast"
import { AuthProvider } from "./context/AuthContext"
import AppRoutes from "./routes/AppRoutes"

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
      <Toaster
        position="top-right"
        toastOptions={{
          className:
            "!rounded-none !border !border-border !bg-card !text-xs !text-card-foreground !shadow-sm",
          duration: 4000,
        }}
      />
    </AuthProvider>
  )
}

export default App
