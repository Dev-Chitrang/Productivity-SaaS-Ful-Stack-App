const ERROR_MAP = {
  ACCOUNT_NOT_FOUND: {
    message: "This account does not exist.\nPlease create an account first.",
    action: "signup",
  },
  WRONG_PASSWORD: {
    message: "Incorrect password.\nPlease try again.",
    clearPassword: true,
  },
  ACCOUNT_INACTIVE: {
    message: "Your account is currently inactive.",
  },
  ACCOUNT_UNVERIFIED: {
    message: "Please verify your email before signing in.",
  },
  OAUTH_ACCOUNT: {
    message: "This account uses Google sign-in.\nPlease sign in with Google.",
  },
}

const NETWORK_ERROR = {
  message: "Unable to connect.\nPlease check your internet connection.",
}

const SERVER_ERROR = {
  message: "Something went wrong.\nPlease try again later.",
}

const DEFAULT_ERROR = {
  message: "Something went wrong.\nPlease try again later.",
}

export function mapAuthError(error) {
  if (!error) return null

  if (!error.response) {
    return { ...NETWORK_ERROR, code: "NETWORK_ERROR" }
  }

  const status = error.response.status
  const detail = error.response.data?.detail

  if (detail && ERROR_MAP[detail]) {
    return { ...ERROR_MAP[detail], code: detail, status }
  }

  if (status >= 500) {
    return { ...SERVER_ERROR, code: "SERVER_ERROR", status }
  }

  return {
    ...DEFAULT_ERROR,
    code: "UNKNOWN",
    status,
    message: detail || DEFAULT_ERROR.message,
  }
}
