import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const formatAxisNumber = (value) => {
  if (value === 0) return '0'
  const absValue = Math.abs(value)
  
  // For very small or very large numbers, use scientific notation
  if (absValue < 1e-4 || absValue > 1e4) {
    const exponent = Math.floor(Math.log10(absValue))
    const mantissa = (value / Math.pow(10, exponent)).toFixed(1)
    return `10^${exponent}`
  }
  
  // For numbers close to 1, show with appropriate decimals
  if (absValue < 1) {
    return value.toFixed(4).replace(/\.?0+$/, '')
  }
  
  return value.toFixed(2).replace(/\.?0+$/, '')
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
            domain={useLogScale ? ['auto', 'auto'] : ['auto', 'auto']}
            allowDataOverflow
            tickFormatter={formatAxisNumber}
          />
          <YAxis 
            label={{ value: yLabel, angle: -90, position: 'insideLeft' }}
            tickFormatter={formatAxisNumber}
          />
          <Tooltip 
            formatter={(value) => value?.toFixed(6)}
            labelFormatter={(label) => `t: ${label?.toFixed(10)}`}
          />
          <Legend />
          {dataKeys.map((key, idx) => (
            <Line
              key={key.key}
              type="monotone"
              dataKey={key.key}
              name={key.name}
              stroke={colors[idx % colors.length]}
              dot={key.dot !== false}
              strokeWidth={key.strokeWidth || 2}
              strokeDasharray={key.dashed ? "5 5" : ""}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
