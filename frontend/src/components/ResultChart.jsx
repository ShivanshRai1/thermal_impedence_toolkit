import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const formatLogAxisNumber = (value) => {
  if (value === 0) return '0'
  const absValue = Math.abs(value)
  
  // For log scale, show powers of 10 with superscript
  if (absValue > 0) {
    const exponent = Math.round(Math.log10(absValue))
    if (Math.abs(Math.log10(absValue) - exponent) < 0.15) {
      // Create superscript format
      const superscriptMap = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', 
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '-': '⁻'
      }
      const expStr = exponent.toString()
      const superscript = expStr.split('').map(c => superscriptMap[c] || c).join('')
      return `10${superscript}`
    }
  }
  return value.toExponential(1)
}

const formatLinearAxisNumber = (value) => {
  if (value === 0) return '0'
  const absValue = Math.abs(value)
  
  // For linear scale, show as decimals
  if (absValue < 0.001) {
    return value.toExponential(2)
  }
  if (absValue < 1) {
    return value.toFixed(4).replace(/\.?0+$/, '')
  }
  if (absValue < 100) {
    return value.toFixed(2).replace(/\.?0+$/, '')
  }
  return value.toFixed(0)
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

const generateLinearTicks = (dataMin, dataMax, numTicks = 6) => {
  if (!dataMin || !dataMax || dataMin >= dataMax) {
    return []
  }
  
  const step = (dataMax - dataMin) / (numTicks - 1)
  const ticks = []
  
  for (let i = 0; i < numTicks; i++) {
    ticks.push(dataMin + i * step)
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
  
  // Get data ranges
  const tpValues = data.map(d => d.tp).filter(t => t > 0)
  const allValues = data.flatMap(d => [
    d.uploadedZth, d.fittedZth, d.Zth, d.refZth, d.predictedZth
  ]).filter(v => v != null && !isNaN(v))
  
  const tpMin = Math.min(...tpValues)
  const tpMax = Math.max(...tpValues)
  const valueMin = Math.min(...allValues)
  const valueMax = Math.max(...allValues)
  
  // Use larger left margin for log scale (for power notation)
  const leftMargin = useLogScale ? 80 : 60
  
  let xTicks, yTicks, xFormatter, yFormatter, xScale, xDomain
  
  if (useLogScale) {
    xTicks = generateLogTicks(tpMin, tpMax)
    yTicks = generateLogTicks(valueMin, valueMax)
    xFormatter = formatLogAxisNumber
    yFormatter = formatLogAxisNumber
    xScale = 'log'
    xDomain = [tpMin * 0.8, tpMax * 1.2]
  } else {
    xTicks = generateLinearTicks(tpMin, tpMax, 8)
    yTicks = generateLinearTicks(valueMin, valueMax, 6)
    xFormatter = formatLinearAxisNumber
    yFormatter = formatLinearAxisNumber
    xScale = 'linear'
    xDomain = [tpMin - (tpMax - tpMin) * 0.05, tpMax + (tpMax - tpMin) * 0.05]
  }

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200">
      {title && <h3 className="text-lg font-semibold mb-3">{title}</h3>}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: leftMargin, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="tp" 
            label={{ value: xLabel, position: 'insideBottom', offset: -5 }}
            scale={xScale}
            domain={xDomain}
            type="number"
            allowDataOverflow={true}
            ticks={xTicks}
            tickFormatter={xFormatter}
          />
          <YAxis 
            label={{ value: yLabel, angle: -90, position: 'insideLeft', offset: -10, dx: -20 }}
            scale={useLogScale ? 'log' : 'linear'}
            domain={useLogScale ? ['auto', 'auto'] : [0, valueMax * 1.1]}
            ticks={useLogScale ? yTicks : undefined}
            tickFormatter={yFormatter}
            width={useLogScale ? 100 : 70}
          />
          <Tooltip 
            formatter={(value) => value != null ? value.toFixed(6) : ''}
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
