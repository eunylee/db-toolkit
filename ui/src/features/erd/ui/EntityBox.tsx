import type { TableLayout } from '../model/layout'
import { HEADER_H, ROW_H } from '../model/layout'

interface Props {
  layout: TableLayout
}

// erd_notation_prototype.jsx의 EntityBox를 실제 테이블/컬럼 데이터 기반으로 옮긴 것.
// 관계선(Unit 5)이 아직 없어 카디널리티 심볼 없이 개체 박스만 그린다.
export function EntityBox({ layout }: Props) {
  const { table, x, y, w, h } = layout

  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={6} fill="white" stroke="#1e293b" strokeWidth={1.5} />
      <rect x={x} y={y} width={w} height={HEADER_H} rx={6} fill="#1e293b" />
      <rect x={x} y={y + HEADER_H - 6} width={w} height={6} fill="#1e293b" />
      <text
        x={x + w / 2}
        y={y + HEADER_H / 2 + 4}
        textAnchor="middle"
        fontSize={13}
        fontWeight={700}
        fill="white"
        letterSpacing={0.5}
      >
        {table.physical_name}
      </text>
      {table.columns.map((col, i) => (
        <text
          key={col.physical_name}
          x={x + 14}
          y={y + HEADER_H + i * ROW_H + 16}
          fontSize={12.5}
          fontWeight={col.is_pk ? 700 : 400}
          fill="#1e293b"
          textDecoration={col.is_pk ? 'underline' : 'none'}
        >
          {col.physical_name}
        </text>
      ))}
    </g>
  )
}
