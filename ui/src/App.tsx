import { ScrapbookGrid } from './features/scrapbook/ui/ScrapbookGrid'
import { TableDesigner } from './features/table-designer/ui/TableDesigner'
import { DomainManagerPage } from './features/domains/ui/DomainManagerPage'

function App() {
  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1>da-toolkit</h1>

      <h2>엑셀 스크랩북 (F-102)</h2>
      <p>엑셀/노션 표를 복사해 아무 셀에나 붙여넣어보세요 (Ctrl+V).</p>
      <ScrapbookGrid />

      <h2 style={{ marginTop: '2rem' }}>테이블 설계 (F-103)</h2>
      <p>논리명을 입력하고 "물리명 제안 적용"을 눌러보세요. "도메인 지정"으로 컬럼 타입을 고를 수 있어요.</p>
      <TableDesigner />

      <h2 style={{ marginTop: '2rem' }}>도메인 관리</h2>
      <p>표준 사전에서 자동 추출된 도메인 + 직접 만든 커스텀 도메인을 관리합니다.</p>
      <DomainManagerPage />
    </main>
  )
}

export default App
