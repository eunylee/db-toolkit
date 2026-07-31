import { ScrapbookGrid } from './features/scrapbook/ui/ScrapbookGrid'

function App() {
  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1>da-toolkit</h1>
      <h2>엑셀 스크랩북 (F-102)</h2>
      <p>엑셀/노션 표를 복사해 아무 셀에나 붙여넣어보세요 (Ctrl+V).</p>
      <ScrapbookGrid />
    </main>
  )
}

export default App
