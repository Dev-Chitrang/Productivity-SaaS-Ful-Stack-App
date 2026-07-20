import axios from 'axios'
import { getAccessToken, setAccessToken, clearAccessToken } from './tokenStore'

const API_BASE_URL = import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api/v1`
    : '/api/v1'

const REFRESH_TIMEOUT_MS = 10000
const QUEUE_TIMEOUT_MS = 15000

const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true,
    timeout: 30000,
})

let isRefreshing = false
let failedQueue = []

function processQueue(error, token = null) {
    failedQueue.forEach(({ resolve, reject }) => {
        if (error) {
            reject(error)
        } else {
            resolve(token)
        }
    })
    failedQueue = []
}

api.interceptors.request.use((config) => {
    const token = getAccessToken()
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        if (error.response?.status !== 401 || originalRequest._retry) {
            return Promise.reject(error)
        }

        if (originalRequest.url?.startsWith('/auth/')) {
            return Promise.reject(error)
        }

        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                const entry = { resolve, reject }
                failedQueue.push(entry)

                setTimeout(() => {
                    const idx = failedQueue.indexOf(entry)
                    if (idx !== -1) {
                        failedQueue.splice(idx, 1)
                        reject(new Error('Token refresh timed out'))
                    }
                }, QUEUE_TIMEOUT_MS)
            }).then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`
                return api(originalRequest)
            })
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
            const { data } = await axios.post(
                `${API_BASE_URL}/auth/refresh`,
                {},
                { withCredentials: true, timeout: REFRESH_TIMEOUT_MS }
            )
            setAccessToken(data.access_token)
            processQueue(null, data.access_token)
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`
            return api(originalRequest)
        } catch (refreshError) {
            processQueue(refreshError, null)
            clearAccessToken()
            if (!window.location.pathname.startsWith('/auth')) {
                window.location.href = '/auth'
            }
            return Promise.reject(refreshError)
        } finally {
            isRefreshing = false
        }
    }
)

export default api
