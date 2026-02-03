// src/components/kpathidea/markerConfig.js

export const PLACE_TYPES = {
  DEFAULT: 0,      // 음식점
  CONCERT: 1,      // 콘서트/축제
  ATTRACTION: 2,   // 명소
};

export const MARKER_STYLES = {
  [PLACE_TYPES.DEFAULT]: {
    label: '음식점',
    emoji: '🍽️',
    width: 45, // 크기 50 -> 45로 약간 축소
    height: 45,
    color: '#ba7676ff', // 이모지 색상: 진한 빨강
    bgColor: '#a56670ff', // 원형 배경: 연한 빨강
   
  },
  [PLACE_TYPES.CONCERT]: {
    label: '콘서트/축제',
    emoji: '🎉',
    width: 45,
    height: 45,
    color: '#e8b37eff', // 이모지 색상: 진한 주황
    bgColor: '#d7a658ff', // 원형 배경: 연한 주황
  
  },
  [PLACE_TYPES.ATTRACTION]: {
    label: '명소',
    emoji: '📍',
    width: 45,
    height: 45,
    color: '#8ab98dff', // 이모지 색상: 진한 초록
    bgColor: '#61a066ff', // 원형 배경: 연한 초록, // 핀 테두리/꼬리: 진한 초록
  },
};

export function createCustomMarkerHTML({
  placeType = 0,
  name,
  markerId,
  isStart = false,
  isEnd = false,
  hasMemo = false,
  memoContent = ''
}) {
  const style = MARKER_STYLES[placeType] || MARKER_STYLES[PLACE_TYPES.DEFAULT];

  // 출발/도착 마커 색상 (유지)
  const borderColor = isStart ? '#4CAF50' : isEnd ? '#F44336' : style.borderColor;
  const bgColor = isStart ? '#C8E6C9' : isEnd ? '#FFCDD2' : style.bgColor;
  const labelBgColor = isStart ? '#4CAF50' : isEnd ? '#F44336' : style.color; // 라벨 배경색은 이모지 색상 사용

  // 🎨 이모지 마커 아이콘 HTML
  const markerIconHTML = `
    <div style="
      position: relative;
      width: ${style.width}px;
      height: ${style.height}px;
    ">
      <div style="
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: ${bgColor};
        border: 1px solid ${borderColor}; /* 4px -> 2px로 두께 감소 */
        border-radius: 50%;
        /* 💡 box-shadow 강도 감소 */
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); 
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <span style="
          font-size: 24px; /* 28px -> 24px로 크기 감소 */
          line-height: 1;
          color: ${style.color || 'black'}; /* 이모지 색상 적용 */
        ">${style.emoji}</span>
      </div>
      
      <div style="
        position: absolute;
        bottom: -10px; /* 핀 꼬리 위치 조정 */
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 10px solid transparent; /* 크기 감소 */
        border-right: 10px solid transparent; /* 크기 감소 */
        border-top: 15px solid ${borderColor}; /* 크기 감소 */
        /* 💡 filter: drop-shadow 강도 감소 */
        filter: drop-shadow(0 1px 2px rgba(0,0,0,0.15));
      "></div>
    </div>
  `;

  return `
    <div class="kpath-custom-marker-wrapper" data-marker-id="${markerId}" style="
      display: flex;
      flex-direction: column;
      align-items: center;
      position: relative;
    ">
      
      ${hasMemo ? `
        <div class="kpath-marker-memo marker-${markerId}" style="
          background: white;
          border: 2px solid ${borderColor}; /* 테두리 3px -> 2px로 감소 */
          border-radius: 8px; /* 10px -> 8px로 감소 */
          padding: 6px 10px;
          margin-bottom: 6px;
          font-size: 11px; /* 12px -> 11px로 감소 */
          max-width: 200px;
          /* 💡 box-shadow 강도 감소 */
          box-shadow: 0 2px 6px rgba(0,0,0,0.15); 
          color: #333;
          font-weight: 400; /* 500 -> 400으로 폰트 무게 감소 */
          line-height: 1.4;
        ">
          ${memoContent.replace(/\n/g, '<br>')}
        </div>
      ` : ''}

      <div class="kpath-marker-label label-${markerId}" style="
        background: ${labelBgColor};
        color: white;
        border: 2px solid white; /* 테두리 3px -> 2px로 감소 */
        border-radius: 14px; /* 16px -> 14px로 감소 */
        padding: 5px 12px; /* 패딩 감소 */
        font-size: 13px; /* 14px -> 13px로 감소 */
        font-weight: 600; /* Bold 대신 600으로 */
        white-space: nowrap;
        margin-bottom: 6px; /* 간격 감소 */
        /* 💡 box-shadow 및 text-shadow 강도 대폭 감소 */
        box-shadow: 0 2px 4px rgba(0,0,0,0.2); 
        text-shadow: 0 1px 2px rgba(0,0,0,0.1); 
        letter-spacing: 0.2px; /* 간격 감소 */
      ">
        ${name}
      </div>

      ${markerIconHTML}

    </div>
  `;
}

export const PLACE_TYPE_OPTIONS = Object.entries(MARKER_STYLES).map(([value, config]) => ({
  value: parseInt(value),
  label: `${config.emoji} ${config.label}`,
  emoji: config.emoji,
}));