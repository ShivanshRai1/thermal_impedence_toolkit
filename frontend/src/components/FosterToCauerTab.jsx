import { useState } from 'react'
import { useData } from '../context/DataContext'
import { useApi } from '../hooks/useApi'
import { ResultChart } from './ResultChart'

export function FosterToCauerTab() {
  const { fosterResult, cauerResult, setCauerResult } = useData()
  const { loading, error, fosterToCauer } = useApi()
  const [localError, setLocalError] = useState(null)

  const handleConvert = async () => {
    if (!fosterResult || !fosterResult.R || !fosterResult.C) {
      setLocalError('Please fit Foster model first')
      return
    }

    setLocalError(null)
    try {
      const result = await fosterToCauer(
        fosterResult.R,
        fosterResult.C,
        fosterResult.fitSeries
      )
      setCauerResult(result)
    } catch (err) {
      setLocalError(err.message)
    }
  }

  // Prepare chart data
  let chartData = []
  if (cauerResult && cauerResult.series) {
    chartData = cauerResult.series.map(p => ({ tp: p.tp, Zth: p.Zth }))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Foster → Cauer</h2>
        <button
          onClick={handleConvert}
          disabled={loading || !fosterResult}
          className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {loading ? 'Converting...' : 'Convert to Cauer'}
        </button>
      </div>

      {(error || localError) && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error || localError}
        </div>
      )}

      {!fosterResult && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded">
          Please complete the "Fit → Foster" step first
        </div>
      )}

      {cauerResult && (
        <>
          {cauerResult.warning && (
            <div className="bg-orange-50 border border-orange-200 text-orange-700 px-4 py-3 rounded">
              {cauerResult.warning}
            </div>
          )}

          <ResultChart
            data={chartData}
            dataKeys={[
              { key: 'Zth', name: 'Cauer Equivalent', dot: false }
            ]}
            title="Cauer Network Response"
          />

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h3 className="font-semibold mb-2">Cauer R, C values</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Index</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">R (K/W)</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">C (J/K)</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {cauerResult.R_cauer?.map((r, idx) => (
                    <tr key={idx}>
                      <td className="px-4 py-2 text-sm text-gray-900">{idx + 1}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{r.toFixed(6)}</td>
                      <td className="px-4 py-2 text-sm text-gray-900">{cauerResult.C_cauer[idx].toFixed(6)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
