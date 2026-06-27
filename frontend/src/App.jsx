import { Toaster } from "react-hot-toast"
import { AuthProvider } from "./context/AuthContext"
import { ThemeProvider } from "./context/ThemeContext"
import AppRoutes from "./routes/AppRoutes"

function App() {
  return (
    <ThemeProvider>
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
    </ThemeProvider>
  )
}

export default App
