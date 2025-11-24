import Papa from 'papaparse'

export function useCsvParser() {
  const parseCsv = (file) => {
    return new Promise((resolve, reject) => {
      Papa.parse(file, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: (results) => {
          try {
            const points = results.data.map((row) => {
              // Look for columns named tp/t/time and Zth/Z
              const tp = row.tp || row.t || row.time || row.Time || row.TP || row.T
              const Zth = row.Zth || row.Z || row.ZTH || row.z
              
              if (tp === undefined || Zth === undefined) {
                throw new Error('CSV must contain columns named "tp" (or "t") and "Zth" (or "Z")')
              }
              
              return { tp: Number(tp), Zth: Number(Zth) }
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
