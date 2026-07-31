import React, { useState, useMemo } from "react";

// ---------------------------------------------------------------------------
// 데이터 모델: 표기법과 무관한 "의미"만 저장한다.
// cardinality: 'one' | 'many'  (해당 끝에서 몇 개까지 붙을 수 있는지 = 최대치)
// optional:    true(선택, 0부터) | false(필수, 1부터)  = 최소치
// ---------------------------------------------------------------------------
const ENTITIES = {
  customer: {
    name: "CUSTOMER",
    x: 40,
    y: 90,
    w: 210,
    attrs: [
      { name: "customer_id", pk: true },
      { name: "name" },
      { name: "email" },
    ],
  },
  order: {
    name: "ORDER",
    x: 400,
    y: 50,
    w: 210,
    attrs: [
      { name: "order_id", pk: true },
      { name: "customer_id", fk: true },
      { name: "order_date" },
      { name: "status" },
    ],
  },
  order_item: {
    name: "ORDER_ITEM",
    x: 760,
    y: 90,
    w: 210,
    attrs: [
      { name: "order_item_id", pk: true },
      { name: "order_id", fk: true },
      { name: "product_id" },
      { name: "qty" },
    ],
  },
};

const RELATIONSHIPS = [
  {
    from: "customer",
    to: "order",
    label: "주문한다",
    // customer 쪽 끝: 주문은 정확히 1명의 고객에 속함 -> one, 필수
    end1: { cardinality: "one", optional: false },
    // order 쪽 끝: 고객은 주문이 0개일 수도, 여러 개일 수도 -> many, 선택
    end2: { cardinality: "many", optional: true },
  },
  {
    from: "order",
    to: "order_item",
    label: "포함한다",
    // order 쪽 끝: 품목은 정확히 1개의 주문에 속함 -> one, 필수
    end1: { cardinality: "one", optional: false },
    // order_item 쪽 끝: 주문은 반드시 1개 이상의 품목을 가짐 -> many, 필수
    end2: { cardinality: "many", optional: false },
  },
];

const ROW_H = 24;
const HEADER_H = 34;
const PAD = 10;

function boxHeight(entity) {
  return HEADER_H + entity.attrs.length * ROW_H + PAD;
}

function anchor(entityKey, side) {
  const e = ENTITIES[entityKey];
  const h = boxHeight(e);
  return side === "right"
    ? { x: e.x + e.w, y: e.y + h / 2 }
    : { x: e.x, y: e.y + h / 2 };
}

// ---- 표기법별 심볼 렌더링 --------------------------------------------------

// 로컬 좌표계: x=0 이 개체 테두리에 맞닿는 지점, +x 방향이 상대 개체 쪽으로
// 멀어지는 방향. 이 그룹 전체를 실제 좌표/각도로 translate+rotate 한다.
function CrowFoot({ color }) {
  return (
    <g stroke={color} strokeWidth="1.8" fill="none">
      <line x1={18} y1={-9} x2={0} y2={0} />
      <line x1={18} y1={0} x2={0} y2={0} />
      <line x1={18} y1={9} x2={0} y2={0} />
    </g>
  );
}
function Bar({ x, color }) {
  return <line x1={x} y1={-8} x2={x} y2={8} stroke={color} strokeWidth="1.8" />;
}
function Circle({ x, color }) {
  return (
    <circle cx={x} cy={0} r={7} fill="white" stroke={color} strokeWidth="1.8" />
  );
}

function IEEnd({ cardinality, optional, color }) {
  return (
    <g>
      {cardinality === "many" ? <CrowFoot color={color} /> : <Bar x={14} color={color} />}
      {optional ? <Circle x={30} color={color} /> : <Bar x={24} color={color} />}
    </g>
  );
}

function BarkerEnd({ cardinality, color }) {
  // Barker: 필수/선택은 선 자체의 실선/점선으로 표현하므로 끝 심볼은
  // '다수(many)'일 때 까마귀발만 그리고, '1(one)'일 때는 아무 심볼도 없다.
  return cardinality === "many" ? <CrowFoot color={color} /> : null;
}

function angleOf(from, to) {
  return (Math.atan2(to.y - from.y, to.x - from.x) * 180) / Math.PI;
}

function RelationshipEdge({ rel, notation }) {
  const a = anchor(rel.from, "right");
  const b = anchor(rel.to, "left");
  const mid = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
  const color = "#334155";

  const angleAtA = angleOf(a, b); // a 끝에서 b쪽을 바라보는 각도
  const angleAtB = angleOf(b, a); // b 끝에서 a쪽을 바라보는 각도

  const dashA = notation === "barker" && rel.end1.optional ? "6 5" : undefined;
  const dashB = notation === "barker" && rel.end2.optional ? "6 5" : undefined;

  return (
    <g>
      <line x1={a.x} y1={a.y} x2={mid.x} y2={mid.y} stroke={color} strokeWidth="1.8" strokeDasharray={dashA} />
      <line x1={mid.x} y1={mid.y} x2={b.x} y2={b.y} stroke={color} strokeWidth="1.8" strokeDasharray={dashB} />

      <text x={mid.x} y={mid.y - 10} textAnchor="middle" fontSize="12" fill="#64748b">
        {rel.label}
      </text>

      <g transform={`translate(${a.x} ${a.y}) rotate(${angleAtA})`}>
        {notation === "ie" ? (
          <IEEnd cardinality={rel.end1.cardinality} optional={rel.end1.optional} color={color} />
        ) : (
          <BarkerEnd cardinality={rel.end1.cardinality} color={color} />
        )}
      </g>
      <g transform={`translate(${b.x} ${b.y}) rotate(${angleAtB})`}>
        {notation === "ie" ? (
          <IEEnd cardinality={rel.end2.cardinality} optional={rel.end2.optional} color={color} />
        ) : (
          <BarkerEnd cardinality={rel.end2.cardinality} color={color} />
        )}
      </g>
    </g>
  );
}

function EntityBox({ entityKey }) {
  const e = ENTITIES[entityKey];
  const h = boxHeight(e);
  return (
    <g>
      <rect x={e.x} y={e.y} width={e.w} height={h} rx={6} fill="white" stroke="#1e293b" strokeWidth="1.5" />
      <rect x={e.x} y={e.y} width={e.w} height={HEADER_H} rx={6} fill="#1e293b" />
      <rect x={e.x} y={e.y + HEADER_H - 6} width={e.w} height={6} fill="#1e293b" />
      <text x={e.x + e.w / 2} y={e.y + HEADER_H / 2 + 4} textAnchor="middle" fontSize="13" fontWeight="700" fill="white" letterSpacing="0.5">
        {e.name}
      </text>
      {e.attrs.map((attr, i) => (
        <g key={attr.name}>
          <text
            x={e.x + 14}
            y={e.y + HEADER_H + i * ROW_H + 16}
            fontSize="12.5"
            fontWeight={attr.pk ? "700" : "400"}
            fontStyle={attr.fk ? "italic" : "normal"}
            fill="#1e293b"
            textDecoration={attr.pk ? "underline" : "none"}
          >
            {attr.name}
            {attr.fk ? " (FK)" : ""}
          </text>
        </g>
      ))}
    </g>
  );
}

function Legend({ notation }) {
  const items =
    notation === "ie"
      ? [
          { key: "one-mandatory", label: "1 (필수, 정확히 1)" },
          { key: "one-optional", label: "1 (선택, 0 또는 1)" },
          { key: "many-mandatory", label: "N (필수, 1 이상)" },
          { key: "many-optional", label: "N (선택, 0 이상)" },
        ]
      : [
          { key: "solid", label: "실선 = 필수 관계" },
          { key: "dashed", label: "점선 = 선택 관계" },
          { key: "foot", label: "까마귀발 = 다수(N)" },
          { key: "noFoot", label: "표시 없음 = 1" },
        ];

  return (
    <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-500 mt-3">
      {items.map((it) => (
        <div key={it.key} className="flex items-center gap-1.5">
          <LegendGlyph notation={notation} kind={it.key} />
          <span>{it.label}</span>
        </div>
      ))}
    </div>
  );
}

function LegendGlyph({ notation, kind }) {
  const color = "#334155";
  const w = 46;
  if (notation === "ie") {
    const map = {
      "one-mandatory": { cardinality: "one", optional: false },
      "one-optional": { cardinality: "one", optional: true },
      "many-mandatory": { cardinality: "many", optional: false },
      "many-optional": { cardinality: "many", optional: true },
    };
    const cfg = map[kind];
    return (
      <svg width={w} height={20} viewBox={`0 0 ${w} 20`}>
        <line x1={0} y1={10} x2={w} y2={10} stroke={color} strokeWidth="1.8" />
        <g transform={`translate(${w} 10) rotate(180)`}>
          <IEEnd cardinality={cfg.cardinality} optional={cfg.optional} color={color} />
        </g>
      </svg>
    );
  }
  if (kind === "solid" || kind === "dashed") {
    return (
      <svg width={w} height={20} viewBox={`0 0 ${w} 20`}>
        <line x1={2} y1={10} x2={w - 2} y2={10} stroke={color} strokeWidth="1.8" strokeDasharray={kind === "dashed" ? "6 5" : undefined} />
      </svg>
    );
  }
  return (
    <svg width={w} height={20} viewBox={`0 0 ${w} 20`}>
      <line x1={0} y1={10} x2={w} y2={10} stroke={color} strokeWidth="1.8" />
      {kind === "foot" && (
        <g transform={`translate(${w} 10) rotate(180)`}>
          <CrowFoot color={color} />
        </g>
      )}
    </svg>
  );
}

export default function ERDNotationPrototype() {
  const [notation, setNotation] = useState("barker");

  const entityKeys = useMemo(() => Object.keys(ENTITIES), []);

  return (
    <div className="w-full bg-slate-50 p-6 rounded-lg font-sans">
      <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
        <div>
          <h2 className="text-base font-bold text-slate-800">ERD 표기법 프로토타입</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            동일한 관계 데이터를 Barker / IE(Crow&apos;s Foot) 두 표기법으로 토글하여 렌더링
          </p>
        </div>
        <div className="inline-flex rounded-lg border border-slate-300 bg-white p-1 text-sm">
          <button
            onClick={() => setNotation("barker")}
            className="px-3 py-1.5 rounded-md font-medium transition-colors"
            style={{
              backgroundColor: notation === "barker" ? "#1e293b" : "transparent",
              color: notation === "barker" ? "white" : "#475569",
            }}
          >
            Barker
          </button>
          <button
            onClick={() => setNotation("ie")}
            className="px-3 py-1.5 rounded-md font-medium transition-colors"
            style={{
              backgroundColor: notation === "ie" ? "#1e293b" : "transparent",
              color: notation === "ie" ? "white" : "#475569",
            }}
          >
            IE (Crow&apos;s Foot)
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <svg viewBox="0 0 1010 260" className="w-full h-auto">
          {RELATIONSHIPS.map((rel, i) => (
            <RelationshipEdge key={i} rel={rel} notation={notation} />
          ))}
          {entityKeys.map((k) => (
            <EntityBox key={k} entityKey={k} />
          ))}
        </svg>
      </div>

      <Legend notation={notation} />

      <p className="text-xs text-slate-400 mt-4 leading-relaxed">
        관계 데이터(cardinality/optional)는 표기법과 무관하게 하나로 저장되고, 렌더링 시점에만 Barker 또는 IE
        심볼로 바뀌어 그려집니다. 새 표기법(예: Chen)을 추가하려면 이 데이터는 그대로 두고 렌더러 하나만
        추가하면 됩니다.
      </p>
    </div>
  );
}
