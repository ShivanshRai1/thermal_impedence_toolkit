import { useState } from 'react'
import { useData } from '../context/DataContext'
import { useApi } from '../hooks/useApi'
import { ResultChart } from './ResultChart'

export function FitFosterTab() {
  const { uploadedPoints, orderN, fosterResult, setFosterResult } = useData()
  const { loading, error, fitFoster } = useApi()
  const [localError, setLocalError] = useState(null)

  const handleFit = async () => {
    if (!uploadedPoints || uploadedPoints.length < 3) {
      setLocalError('Please upload a CSV file with at least 3 data points')
      return
    }

    setLocalError(null)
    try {
      const result = await fitFoster(uploadedPoints, orderN)
      setFosterResult(result)
    } catch (err) {
      setLocalError(err.message)
    }
  }

  // Prepare chart data
  let chartData = []
  if (uploadedPoints && fosterResult) {
    // Merge uploaded points and fitted curve
    const pointsMap = new Map(uploadedPoints.map(p => [p.tp, { ...p, uploadedZth: p.Zth }]))
    
    fosterResult.fitSeries?.forEach(p => {
      if (pointsMap.has(p.tp)) {
        pointsMap.get(p.tp).fittedZth = p.Zth
      } else {
        pointsMap.set(p.tp, { tp: p.tp, fittedZth: p.Zth })
      }
    })
    
    chartData = Array.from(pointsMap.values()).sort((a, b) => a.tp - b.tp)
  } else if (uploadedPoints) {
    chartData = uploadedPoints.map(p => ({ tp: p.tp, uploadedZth: p.Zth }))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Fit → Foster</h2>
        <button
          onClick={handleFit}
          disabled={loading || !uploadedPoints}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {loading ? 'Fitting...' : 'Fit Foster'}
        </button>
      </div>

      {(error || localError) && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error || localError}
        </div>
      )}

      <ResultChart
        data={chartData}
        dataKeys={[
          { key: 'uploadedZth', name: 'Uploaded Points', dot: true },
          { key: 'fittedZth', name: 'Fitted Curve', dot: false, strokeWidth: 2 }
        ]}
        title="Zth vs Time"
      />

      {fosterResult && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="font-semibold mb-2">Foster R, C values</h3>
          {fosterResult.warning && (
            <p className="text-orange-600 text-sm mb-2">{fosterResult.warning}</p>
          )}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Index</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">R (K/W)</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">C (J/K)</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">τ (s)</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {fosterResult.R?.map((r, idx) => (
                  <tr key={idx}>
                    <td className="px-4 py-2 text-sm text-gray-900">{idx + 1}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{r.toFixed(6)}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{fosterResult.C[idx].toFixed(6)}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{(r * fosterResult.C[idx]).toFixed(6)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
