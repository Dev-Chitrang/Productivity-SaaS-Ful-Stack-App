import { Component } from "react"

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error("[ErrorBoundary]", error, info.componentStack)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="mx-auto flex max-w-md flex-col items-center justify-center px-4 py-16 text-center">
          <h2 className="mb-2 text-base font-semibold text-foreground">Something went wrong</h2>
          <p className="mb-4 text-xs text-muted-foreground">
            {this.state.error?.message || "An unexpected error occurred."}
          </p>
          <button
            className="rounded border border-border bg-background px-4 py-2 text-xs font-medium text-foreground hover:bg-accent"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
