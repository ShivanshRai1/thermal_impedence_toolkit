import Papa from 'papaparse'

export function useCsvParser() {
  const parseCsv = (file) => {
    return new Promise((resolve, reject) => {
      Papa.parse(file, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        transformHeader: (h) => h.trim().toLowerCase(),
        complete: (results) => {
          try {
            const points = results.data.map((row) => {
              // Normalize keys - trim and lowercase
              const normalizedRow = {}
              for (const key in row) {
                normalizedRow[key.trim().toLowerCase()] = row[key]
              }
              
              // Look for columns named tp/t/time and zth/z
              const tp = normalizedRow.tp || normalizedRow.t || normalizedRow.time
              const zth = normalizedRow.zth || normalizedRow.z
              
              if (tp === undefined || zth === undefined) {
                throw new Error('CSV must contain columns named "tp" (or "t") and "Zth" (or "Z")')
              }
              
              return { tp: Number(tp), Zth: Number(zth) }
            }).filter(p => !isNaN(p.tp) && !isNaN(p.Zth) && p.tp > 0)
            
            if (points.length === 0) {
              throw new Error('No valid data points found in CSV')
            }
            
            // Sort by time
            points.sort((a, b) => a.tp - b.tp)
            
            resolve(points)
          } catch (error) {
            reject(error)
          }
        },
        error: (error) => {
          reject(error)
        }
      })
    })
  }

  return { parseCsv }
}
