import { useState } from 'react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export function useApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fitFoster = async (points, N) => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(`${API_BASE_URL}/api/fit_foster`, {
        points,
        N: Number(N)
      })
      setLoading(false)
      return response.data
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message
      setError(errorMsg)
      setLoading(false)
      throw new Error(errorMsg)
    }
  }

  const fosterToCauer = async (R, C, series) => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(`${API_BASE_URL}/api/foster_to_cauer`, {
        R,
        C,
        series
      })
      setLoading(false)
      return response.data
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message
      setError(errorMsg)
      setLoading(false)
      throw new Error(errorMsg)
    }
  }

  const predict = async (points, Aref, Anew) => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post(`${API_BASE_URL}/api/predict`, {
        points,
        Aref: Number(Aref),
        Anew: Number(Anew)
      })
      setLoading(false)
      return response.data
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message
      setError(errorMsg)
      setLoading(false)
      throw new Error(errorMsg)
    }
  }

  return {
    loading,
    error,
    fitFoster,
    fosterToCauer,
    predict
  }
}
