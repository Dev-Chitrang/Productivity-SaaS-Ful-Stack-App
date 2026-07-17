import axios from 'axios'
import { getAccessToken, setAccessToken, clearAccessToken } from './tokenStore'

const api = axios.create({
    baseURL: `${import.meta.env.VITE_API_URL}/api/v1`,
    withCredentials: true
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
                failedQueue.push({ resolve, reject })
            }).then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`
                return api(originalRequest)
            })
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
            const { data } = await axios.post(
                `${import.meta.env.VITE_API_URL}/api/v1/auth/refresh`,
                {},
                { withCredentials: true }
            )
            setAccessToken(data.access_token)
            processQueue(null, data.access_token)
            originalRequest.headers.Authorization = `Bearer ${data.access_token}`
            return api(originalRequest)
        } catch (refreshError) {
            processQueue(refreshError, null)
            clearAccessToken()
            window.location.href = '/auth'
            return Promise.reject(refreshError)
        } finally {
            isRefreshing = false
        }
    }
)

export default api
