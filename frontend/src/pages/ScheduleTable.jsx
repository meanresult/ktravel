import React, { useState, useEffect } from 'react';
import { Trash2 } from 'lucide-react'; // 🗑️ 삭제 아이콘 추가
import '../styles/ScheduleTable.css';

// ⭐ onDayTitleChange prop 추가
const ScheduleTable = ({ scheduleId, onDayTitleChange }) => {
    const [token, setToken] = useState(localStorage.getItem('session_id'));
    
    const [dayTitles, setDayTitles] = useState([]);
    const [selectedDayTitle, setSelectedDayTitle] = useState('');
    const [description, setDescription] = useState('');
    const [authError, setAuthError] = useState(null);
    
    // ⭐ 편집 상태 관리
    const [isDeleteMode, setIsDeleteMode] = useState(false); // 행 삭제 모드 상태

    // 💡 일정 테이블 항목/시간 상태로 관리
    const initialDays = ['Location', 'Estimated Cost', 'Place of use', 'Memo', 'Notice'];
    const initialTimes = ['9:00', '10:00', '11:00'];
    const [scheduleTimes, setScheduleTimes] = useState(initialTimes);
    const [scheduleDays, setScheduleDays] = useState(initialDays);
    
    // ⭐ 셀 데이터 상태 관리 (time x day)
    const [cellData, setCellData] = useState({});
    
    const fetchWithAuth = async (url, options = {}) => {
        setAuthError(null);

        if (!token) {
            const error = new Error("세션이 없습니다. 로그인해주세요");
            setAuthError(error.message);
            throw error; 
        }

        const headers = {
            ...options.headers,
            Authorization: `Bearer ${token}`, 
            'Content-Type': 'application/json'
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                const error = new Error('로그인이 만료되었습니다. 다시 로그인해주세요.');
                setAuthError(error.message); 
                localStorage.removeItem('session_id');
                setToken(null);

                setTimeout(() => {
                    window.location.href = '/'; 
                }, 2000); 

                throw error;
            }
            
            if (!response.ok) {
                const errorDetail = await response.json().catch(() => ({}));
                const errorMessage = errorDetail.detail || `API 요청 실패: ${response.status} ${response.statusText}`;
                throw new Error(errorMessage);
            }

            return response;

        } catch (error) {
            console.error("❌ fetch 실패:", error);
            throw error;
        }
    };

    // 1️⃣ day_titles 가져오기
    useEffect(() => {
        if (!token) return; 

        console.log("🔍 day_titles API 호출 시작");
        
        fetchWithAuth('http://localhost:8000/api/schedules/day_titles')
          .then(res => res.json())
          .then(data => {
            console.log("✅ day_titles 응답 데이터:", data);
            
            setDayTitles(data.map(d => d.day_title)); 
            
            if (data.length > 0) {
                setSelectedDayTitle(data[0].day_title);
                console.log("✅ 첫 번째 day_title 선택:", data[0].day_title);
                
                // ⭐ 첫 번째 일정 선택 시 부모에게 알림
                if (onDayTitleChange) {
                    onDayTitleChange(data[0].day_title);
                }
            } else {
                console.warn("⚠️ No day Title");
            }
          })
          .catch(err => {
            console.error("❌ day_titles fetch 실패:", err.message);
          });
          
    }, [token]);

    // 2️⃣ schedule 상세 가져오기
    useEffect(() => {
      if (!scheduleId || !token) return;

      console.log(`🔍 Schedule ${scheduleId} 상세 정보 가져오기`);

      fetchWithAuth(`http://localhost:8000/api/schedules/${scheduleId}`)
        .then(res => res.json())
        .then(data => {
          console.log("✅ Schedule 상세 데이터:", data);
          if (data.day_title) {
            setSelectedDayTitle(data.day_title);
            // ⭐ 부모에게 알림
            if (onDayTitleChange) {
                onDayTitleChange(data.day_title);
            }
          }
          if (data.description) setDescription(data.description);
        })
        .catch(err => console.error("❌ Schedule fetch 실패:", err.message));
        
    }, [scheduleId, token]);

    // 3️⃣ 선택된 day_title에 따른 description 갱신
    useEffect(() => {
        if (!selectedDayTitle || !token) return;
        
        console.log(`🔍 ${selectedDayTitle}의 description 가져오기`);
        
        fetchWithAuth(
          `http://localhost:8000/api/schedules/description?day_title=${encodeURIComponent(selectedDayTitle)}`
        )
          .then(res => res.json())
          .then(data => {
            console.log("✅ description 데이터:", data);
            setDescription(data.description || '');
          })
          .catch(err => console.error("❌ description fetch 실패:", err.message));
          
    }, [selectedDayTitle, token]);

    // 4️⃣ description 저장
    const handleSave = () => {
        if (!selectedDayTitle || !token) return;

        console.log(`💾 저장 시작: ${selectedDayTitle}`);

        fetchWithAuth(
          `http://localhost:8000/api/schedules/update_description?day_title=${encodeURIComponent(selectedDayTitle)}&description=${encodeURIComponent(description)}`,
          { method: "PUT" }
        )
          .then(res => res.json())
          .then((data) => {
            console.log("✅ 저장 성공:", data);
            alert("✅ 저장되었습니다!");
          })
          .catch(err => {
            console.error("❌ 저장 실패", err.message);
            if (!authError) {
              alert(`❌ 저장 실패: ${err.message}`);
            }
          });
    };

    // ⭐ day_title 변경 핸들러
    const handleDayTitleChange = (e) => {
        const newDayTitle = e.target.value;
        setSelectedDayTitle(newDayTitle);
        
        // 부모 컴포넌트에 변경 알림
        if (onDayTitleChange) {
            onDayTitleChange(newDayTitle);
        }
    };
    
    // ----------------------------------------------------
    // ⭐ 셀 데이터 관리 함수
    // ----------------------------------------------------
    
    // 셀 값 가져오기
    const getCellValue = (time, day) => {
        const key = `${time}-${day}`;
        return cellData[key] || '';
    };
    
    // 셀 값 변경하기
    const handleCellChange = (time, day, value) => {
        const key = `${time}-${day}`;
        setCellData(prev => ({
            ...prev,
            [key]: value
        }));
    };
    
    // ----------------------------------------------------
    // ⭐ 행(시간) 관리 함수 개선
    // ----------------------------------------------------
    
    // 5️⃣ 행 추가 (자동 시간 계산)
    const handleAddRow = () => {
        const sortedTimes = [...scheduleTimes].sort((a, b) => {
            return new Date(`2000/01/01 ${a}`) - new Date(`2000/01/01 ${b}`);
        });
        
        let newTime;
        if (sortedTimes.length > 0) {
            const lastTimeStr = sortedTimes[sortedTimes.length - 1];
            const [hourStr, minuteStr] = lastTimeStr.split(':');
            let hour = parseInt(hourStr);
            let minute = parseInt(minuteStr);
            
            // 1시간 추가 로직
            hour = (hour + 1) % 24; 
            
            newTime = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
        } else {
            newTime = '09:00'; 
        }

        if (scheduleTimes.includes(newTime)) {
             // 시간이 이미 존재하면 다음 분으로 이동 (간단한 충돌 회피)
             const [hourStr, minuteStr] = newTime.split(':');
             const minute = parseInt(minuteStr) + 1;
             newTime = `${hourStr}:${String(minute).padStart(2, '0')}`;
        }


        const updatedTimes = [...scheduleTimes, newTime].sort((a, b) => {
            return new Date(`2000/01/01 ${a}`) - new Date(`2000/01/01 ${b}`);
        });
        setScheduleTimes(updatedTimes);
        alert(`✅ ${newTime} row has been added.`);
    };
    
    // 6️⃣ 행 삭제 모드 전환
    const handleDeleteRowMode = () => {
        setIsDeleteMode(!isDeleteMode);
        if (!isDeleteMode) {
            alert("🗑️ The row delete mode is on. Click the time cell you want to delete.");
        } else {
            alert("✅ The row delete mode has been turned off.");
        }
    };
    
    // 7️⃣ 특정 행 삭제 (시간 셀 클릭 시)
    const handleRemoveTimeSlot = (timeToRemove) => {
        if (!isDeleteMode) return;

        if (window.confirm(`Are you sure you want to delete the ${timeToRemove} line?`)) {
            setScheduleTimes(scheduleTimes.filter(time => time !== timeToRemove));
            alert(`✅ ${timeToRemove} row has been deleted.`);
        }
    };
    
    // ----------------------------------------------------
    // ⭐ 열(항목) 관리 함수
    // ----------------------------------------------------
    
    // 8️⃣ 열 추가
    const handleAddColumn = () => {
        const newColumn = prompt("Enter the name of the item (column name) to be added:");
        if (newColumn && !scheduleDays.includes(newColumn)) {
            setScheduleDays([...scheduleDays, newColumn]);
            alert(`✅ '${newColumn}' Column added.`);
        } else if (newColumn) {
            alert("⚠️ Item name that already exists.");
        }
    };
    
    // 9️⃣ 열 삭제
    const handleDeleteColumn = () => {
        const columnToRemove = prompt(`Enter the name of the item to delete (${scheduleDays.join(', ')}):`);
        if (columnToRemove && scheduleDays.includes(columnToRemove)) {
            if (window.confirm(`Are you sure you want to delete column '${columnToRemove}'?`)) {
                setScheduleDays(scheduleDays.filter(day => day !== columnToRemove));
                alert(`✅ '${columnToRemove}' Column deleted.`);
            }
        } else if (columnToRemove) {
             alert("⚠️ 해당 항목 이름이 목록에 없습니다.");
        }
    };
    
    // ----------------------------------------------------
    // ⭐ CSV 다운로드 함수
    // ----------------------------------------------------
    
      const handleDownloadCSV = () => {
          const header = ["Time", ...scheduleDays].join(",");
          
          const rows = scheduleTimes.map(time => {
              const safeTime = `${time}`; // 시간 텍스트로 강제
          
              const rowData = scheduleDays.map(day => {
                  let value = getCellValue(time, day) || "";
                  
                  // 쉼표, 따옴표 포함 시 이스케이프
                  if (value.includes(',') || value.includes('"')) {
                      value = `"${value.replace(/"/g, '""')}"`;
                  }

                  // 엑셀이 날짜/숫자처럼 오해하지 않도록
                  if (!value.startsWith('"')) {
                      value = `"${value}"`;
                  }

                  return value;
              });

              return [safeTime, ...rowData].join(",");
          });

          const csvContent = [header, ...rows].join("\n");

          // ✅ UTF-8 with BOM 추가 → 한글 깨짐 해결!
          const BOM = "\uFEFF";
          const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });

          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.setAttribute('href', url);
          link.setAttribute('download', `${selectedDayTitle || 'Schedule'}_Details.csv`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);

          alert(`📥 '${selectedDayTitle || 'Schedule'}_Details.csv' 다운로드가 시작되었습니다.`);
      };



    return (
        <div className="kschedule-container">
            <header className="kschedule-header">
                <h1>🗓️ Schedule Management and Editor</h1>
            </header>

            {authError && (
                <div className="kdh-error-message">
                    <p>🛑 **에러:** {authError}</p>
                    {authError.includes('로그인') && (
                        <p>잠시 후 메인 페이지로 이동합니다...</p>
                    )}
                </div>
            )}

            {!authError && (
                <>
                    {/* 상단: Day Title, Description, Save */}
                    <div className="kschedule-details">
                        <label>Day Title</label>
                        <select
                          className="kschedule-select"
                          value={selectedDayTitle}
                          onChange={handleDayTitleChange}
                        >
                            {dayTitles.length === 0 && (
                                <option value="">No Schedule!</option>
                            )}
                            {dayTitles.map((day, idx) => (
                                <option key={idx} value={day}>{day}</option>
                            ))}
                        </select>

                        <label>Description</label>
                        <textarea
                          rows={1}
                          value={description}
                          onChange={(e) => setDescription(e.target.value)}
                        />

                        <button className="kschedule-btn-success" onClick={handleSave}>
                            ✅ Save
                        </button>
                    </div>
                    
                    {/* ⭐ 툴바: 행 관리, 열 관리 및 CSV 버튼 */}
                    <div className="kschedule-toolbar">
                        {/* 행 추가 버튼 */}
                        <button 
                            onClick={handleAddRow} 
                            className="kschedule-btn-primary"
                        >
                            ➕ Add Row
                        </button>
                        
                        {/* 행 삭제 모드 버튼 */}
                        <button 
                            onClick={handleDeleteRowMode} 
                            style={{ 
                                background: isDeleteMode ? '#ef4444' : '#cc0000', 
                                color: 'white'
                            }}
                            className="kschedule-btn-danger"
                        >
                            <Trash2 size={16} style={{ marginRight: isDeleteMode ? '0' : '0.5rem' }} /> 
                            {isDeleteMode ? 'Delete Row Mode (ON)' : 'Delete Row Mode (OFF)'}
                        </button>
                        
                        {/* 열 추가 버튼 */}
                        <button 
                            onClick={handleAddColumn} 
                            className="kschedule-btn-secondary"
                        >
                            ➕ Add Columns 
                        </button>
                        
                        {/* 열 삭제 버튼 */}
                        <button 
                            onClick={handleDeleteColumn} 
                            className="kschedule-btn-secondary-danger"
                        >
                            ➖ Delete Columns
                        </button>

                        {/* CSV 다운로드 버튼 */}
                        <button 
                            onClick={handleDownloadCSV} 
                            className="kschedule-btn-info"
                        >
                            📥 CSV Download
                        </button>
                    </div>

                    {/* 테이블 */}
                    <div className="kschedule-table-wrapper">
                        <table className="kschedule-table">
                            <thead>
                                <tr>
                                    <th className={isDeleteMode ? 'kschedule-delete-mode' : ''}>Time</th>
                                    {scheduleDays.map((day, idx) => <th key={idx}>{day}</th>)}
                                </tr>
                            </thead>
                            <tbody>
                                {scheduleTimes.map((time, ti) => (
                                    <tr key={ti}>
                                        <td 
                                            className={`kschedule-time-cell ${isDeleteMode ? 'kschedule-time-cell-deletable' : ''}`}
                                            onClick={() => handleRemoveTimeSlot(time)}
                                        >
                                            {time}
                                        </td>
                                        {scheduleDays.map((day, di) => (
                                            <td 
                                                key={di} 
                                                className="kschedule-schedule-cell"
                                            >
                                                <input
                                                    type="text"
                                                    value={getCellValue(time, day)}
                                                    onChange={(e) => handleCellChange(time, day, e.target.value)}
                                                    className="kschedule-cell-input"
                                                    placeholder=" "
                                                />
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
};

export default ScheduleTable;