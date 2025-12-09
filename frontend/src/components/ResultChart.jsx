import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const formatAxisNumber = (value) => {
  if (value === 0) return '0'
  const absValue = Math.abs(value)
  
  // For log scale, show powers of 10
  if (absValue > 0) {
    const exponent = Math.round(Math.log10(absValue))
    if (Math.abs(Math.log10(absValue) - exponent) < 0.2) {
      return `10^${exponent}`
    }
  }
  
  // For very small numbers
  if (absValue < 1e-4) {
    return value.toExponential(1)
  }
  
  // For normal range numbers
  if (absValue < 1) {
    return value.toFixed(4).replace(/\.?0+$/, '')
  }
  
  return value.toFixed(2).replace(/\.?0+$/, '')
}

const generateLogTicks = (dataMin, dataMax) => {
  if (!dataMin || !dataMax || dataMin <= 0 || dataMax <= 0) {
    return []
  }
  
  const minExp = Math.floor(Math.log10(dataMin))
  const maxExp = Math.ceil(Math.log10(dataMax))
  
  const ticks = []
  for (let i = minExp; i <= maxExp; i++) {
    ticks.push(Math.pow(10, i))
  }
  return ticks
}

export function ResultChart({ data, dataKeys, title, xLabel = "Time (s)", yLabel = "Zth (K/W)", useLogScale = true }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">No data to display</p>
      </div>
    )
  }

  const colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
  
  // Get data range for ticks
  const tpValues = data.map(d => d.tp).filter(t => t > 0)
  const dataMin = Math.min(...tpValues)
  const dataMax = Math.max(...tpValues)
  const logTicks = useLogScale ? generateLogTicks(dataMin, dataMax) : undefined

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      {title && <h3 className="text-lg font-semibold mb-3">{title}</h3>}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="tp" 
            label={{ value: xLabel, position: 'insideBottom', offset: -5 }}
            scale={useLogScale ? "log" : "linear"}
            domain={useLogScale ? [Math.min(...tpValues) * 0.8, Math.max(...tpValues) * 1.2] : ['auto', 'auto']}
            type="number"
            allowDataOverflow={true}
            ticks={useLogScale ? logTicks : undefined}
            tickFormatter={formatAxisNumber}
          />
          <YAxis 
            label={{ value: yLabel, angle: -90, position: 'insideLeft' }}
            tickFormatter={formatAxisNumber}
          />
          <Tooltip 
            formatter={(value) => value?.toFixed(6)}
            labelFormatter={(label) => {
              if (label === null || label === undefined) return ''
              return `t: ${label.toExponential(3)}`
            }}
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
          />
          <Legend />
          {dataKeys.map((key, idx) => (
            <Line
              key={key.key}
              type="monotone"
              dataKey={key.key}
              name={key.name}
              stroke={colors[idx % colors.length]}
              dot={key.dot !== false ? { r: 3 } : false}
              strokeWidth={key.strokeWidth || 2}
              strokeDasharray={key.dashed ? "5 5" : ""}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
