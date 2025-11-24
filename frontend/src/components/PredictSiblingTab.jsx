import { useState } from 'react'
import { useData } from '../context/DataContext'
import { useApi } from '../hooks/useApi'
import { ResultChart } from './ResultChart'

export function PredictSiblingTab() {
  const { uploadedPoints, refArea, newArea, predictResult, setPredictResult } = useData()
  const { loading, error, predict } = useApi()
  const [localError, setLocalError] = useState(null)

  const handlePredict = async () => {
    if (!uploadedPoints || uploadedPoints.length === 0) {
      setLocalError('Please upload a CSV file first')
      return
    }

    if (!newArea || parseFloat(newArea) <= 0) {
      setLocalError('Please enter a valid New Die Area')
      return
    }

    setLocalError(null)
    try {
      const result = await predict(uploadedPoints, refArea, newArea)
      setPredictResult(result)
    } catch (err) {
      setLocalError(err.message)
    }
  }

  // Prepare chart data
  let chartData = []
  if (uploadedPoints && predictResult) {
    const pointsMap = new Map(uploadedPoints.map(p => [p.tp, { ...p, refZth: p.Zth }]))
    
    predictResult.series?.forEach(p => {
      if (pointsMap.has(p.tp)) {
        pointsMap.get(p.tp).predictedZth = p.Zth
      } else {
        pointsMap.set(p.tp, { tp: p.tp, predictedZth: p.Zth })
      }
    })
    
    chartData = Array.from(pointsMap.values()).sort((a, b) => a.tp - b.tp)
  } else if (uploadedPoints) {
    chartData = uploadedPoints.map(p => ({ tp: p.tp, refZth: p.Zth }))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Predict Sibling</h2>
        <button
          onClick={handlePredict}
          disabled={loading || !uploadedPoints || !newArea}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {loading ? 'Predicting...' : 'Predict Sibling'}
        </button>
      </div>

      {(error || localError) && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error || localError}
        </div>
      )}

      {!uploadedPoints && (
        <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded">
          Please upload a CSV file first
        </div>
      )}

      <ResultChart
        data={chartData}
        dataKeys={[
          { key: 'refZth', name: 'Reference Package', dot: true },
          { key: 'predictedZth', name: 'Predicted Package', dot: true, dashed: true }
        ]}
        title="Package Comparison"
      />

      {predictResult && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="font-semibold mb-2">Prediction Summary</h3>
          <div className="space-y-2 text-sm">
            <p><span className="font-medium">Scaling Factor:</span> {predictResult.scale?.toFixed(6)}</p>
            <p><span className="font-medium">Reference Area:</span> {refArea}</p>
            <p><span className="font-medium">New Area:</span> {newArea}</p>
            {predictResult.summary && (
              <p className="text-gray-600 mt-2">{predictResult.summary}</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
