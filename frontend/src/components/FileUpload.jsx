import { useState } from 'react'
import { useData } from '../context/DataContext'
import { useCsvParser } from '../hooks/useCsvParser'

export function FileUpload() {
  const { setUploadedPoints, setFosterResult, setCauerResult, setPredictResult } = useData()
  const { parseCsv } = useCsvParser()
  const [fileName, setFileName] = useState('')
  const [error, setError] = useState(null)

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setFileName(file.name)
    setError(null)
    
    // Clear previous results
    setFosterResult(null)
    setCauerResult(null)
    setPredictResult(null)

    try {
      const points = await parseCsv(file)
      setUploadedPoints(points)
      setError(null)
    } catch (err) {
      setError(err.message)
      setUploadedPoints(null)
    }
  }

  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        1) Load Zth vs t (CSV)
      </label>
      <input
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
      />
      {fileName && (
        <p className="text-xs text-gray-600 mt-1">
          Loaded: {fileName}
        </p>
      )}
      {error && (
        <p className="text-xs text-red-600 mt-1">
          {error}
        </p>
      )}
      <p className="text-xs text-gray-500 mt-1">
        CSV must contain columns named <code className="bg-gray-100 px-1">tp</code> (or <code className="bg-gray-100 px-1">t</code>) and <code className="bg-gray-100 px-1">Zth</code> (or <code className="bg-gray-100 px-1">Z</code>). Case-insensitive.
      </p>
    </div>
  )
}
