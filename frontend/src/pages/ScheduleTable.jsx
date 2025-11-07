import React, { useState, useEffect, useCallback } from 'react';
import { Trash2 } from 'lucide-react'; 
import '../styles/ScheduleTable.css';
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

// ✅ 컴포넌트 외부 함수: 인증 기반 Fetch 로직
const globalFetchWithAuth = async (url, options = {}, token, setToken, setAuthError) => {
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
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            const error = new Error('로그인이 만료되었습니다. 다시 로그인해주세요.');
            setAuthError(error.message);
            localStorage.removeItem('session_id');
            setToken(null);
            setTimeout(() => { window.location.href = '/'; }, 2000);
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

const createNewRow = () => ({
    id: `row-${Date.now()}-${Math.floor(Math.random() * 10000)}`,
    label: ''
});

const ScheduleTable = ({ scheduleId, onDayTitleChange }) => {
    const [token, setToken] = useState(localStorage.getItem('session_id'));
    const [dayTitles, setDayTitles] = useState([]);
    const [selectedDayTitle, setSelectedDayTitle] = useState('');
    const [description, setDescription] = useState('');
    const [authError, setAuthError] = useState(null);
    const [isLoadingDestinations, setIsLoadingDestinations] = useState(false);

    const [isDeletionModeActive, setIsDeletionModeActive] = useState(false);

    const initialDays = ['Time','Location', 'Estimated Cost', 'Memo', 'Notice'];
    const initialRows = [createNewRow(), createNewRow(), createNewRow()];
    
    const [scheduleRows, setScheduleRows] = useState(initialRows);
    const [scheduleDays, setScheduleDays] = useState(initialDays);
    const [cellData, setCellData] = useState({});

    const fetchWithAuth = useCallback((url, options = {}) =>
        globalFetchWithAuth(url, options, token, setToken, setAuthError),
    [token]);

    const fetchDestinations = useCallback(async () => {
        if (!selectedDayTitle || !token) return;
        setIsLoadingDestinations(true);

        try {
            const response = await fetchWithAuth(
                `http://localhost:8000/api/destinations/by-schedule?day_title=${encodeURIComponent(selectedDayTitle)}`
            );
            const destinations = await response.json();
            const numDestinations = destinations.length;
            const locationColumnName = 'Location';

            let newLocationData = {};
            let newRowsArray = [];

            setScheduleRows(prevRows => {
                for (let i = 0; i < numDestinations; i++) {
                    if (i < prevRows.length) {
                        newRowsArray.push(prevRows[i]);
                    } else {
                        newRowsArray.push(createNewRow());
                    }
                }
                return newRowsArray;
            });

            newRowsArray.forEach((row, i) => {
                const key = `${row.id}-${locationColumnName}`;
                newLocationData[key] = destinations[i]?.name || "";
            });

            setCellData(prev => ({
                ...prev,
                ...newLocationData
            }));
        } catch (error) {
            console.error("❌ 목적지 조회 실패:", error.message);
        } finally {
            setIsLoadingDestinations(false);
        }
    }, [selectedDayTitle, token, fetchWithAuth]);

    useEffect(() => {
        fetchDestinations();
    }, [fetchDestinations]);

    useEffect(() => {
        if (!token) return;
        fetchWithAuth('http://localhost:8000/api/schedules/day_titles')
            .then(res => res.json())
            .then(data => {
                setDayTitles(data.map(d => d.day_title));
                if (data.length > 0 && !selectedDayTitle) {
                    setSelectedDayTitle(data[0].day_title);
                    if (onDayTitleChange) onDayTitleChange(data[0].day_title);
                }
            })
            .catch(err => console.error(err.message));
    }, [token, fetchWithAuth, onDayTitleChange]);

    useEffect(() => {
        if (!scheduleId || !token) return;

        fetchWithAuth(`http://localhost:8000/api/schedules/${scheduleId}`)
            .then(res => res.json())
            .then(data => {
                setSelectedDayTitle(data.day_title || '');
                onDayTitleChange(data.day_title);
                setDescription(data.description || '');
            })
            .catch(console.error);
    }, [scheduleId, token]);

    useEffect(() => {
        if (!selectedDayTitle || !token) return;
        fetchWithAuth(
            `http://localhost:8000/api/schedules/description?day_title=${encodeURIComponent(selectedDayTitle)}`
        )
            .then(res => res.json())
            .then(data => {
                setDescription(data.description || '');
            })
            .catch(console.error);
    }, [selectedDayTitle, token]);

    const handleSave = () => {};

    const handleDayTitleChange = (e) => {
        setSelectedDayTitle(e.target.value);
        if (onDayTitleChange) onDayTitleChange(e.target.value);
    };

    const getCellValue = (rowId, day) => {
        return cellData[`${rowId}-${day}`] || '';
    };

    const handleCellChange = (rowId, day, value) => {
        setCellData(prev => ({
            ...prev,
            [`${rowId}-${day}`]: value
        }));
    };

    const handleAddRow = () => {
        setScheduleRows(prev => [...prev, createNewRow()]);
    };

    const toggleDeletionMode = () =>
        setIsDeletionModeActive(prev => !prev);

    const handleRemoveRow = useCallback((rowId) => { 
        if (!isDeletionModeActive) return;
        if (window.confirm("Are you sure you want to delete this?")) {
            setScheduleRows(prev => prev.filter(row => row.id !== rowId));
            setCellData(prev => {
                const newData = {...prev};
                scheduleDays.forEach(day => delete newData[`${rowId}-${day}`]);
                return newData;
            });
        }
    }, [isDeletionModeActive, scheduleDays]);

    const handleRemoveColumn = (column) => {
        if (!isDeletionModeActive) return;
        if (window.confirm("Are you sure you want to delete this?")) {
            setScheduleDays(prev => prev.filter(day => day !== column));
            setCellData(prev => {
                const newData = {...prev};
                scheduleRows.forEach(row => delete newData[`${row.id}-${column}`]);
                return newData;
            });
        }
    };

    const handleAddColumn = () => {
        const newColumn = prompt("Enter items to add:");
        if (newColumn && !scheduleDays.includes(newColumn)) {
            setScheduleDays([...scheduleDays, newColumn]);
        } else if (newColumn) {
            alert("It already exists.");
        }
    };

    const handleDownloadCSV = () => {
        const header = ["No.", ...scheduleDays].join(",");
        
        const rows = scheduleRows.map((rowItem, ri) => {
            const safeRowIndex = `${ri + 1}`;
            
            const rowData = scheduleDays.map(day => {
                let value = getCellValue(rowItem.id, day) || "";
                if (value.includes(',') || value.includes('"')) {
                    value = `"${value.replace(/"/g, '""')}"`;
                }
                if (!value.startsWith('"') && value.trim().length > 0) {
                    value = `"${value}"`;
                }
                return value;
            });
            return [safeRowIndex, ...rowData].join(",");
        });

        const csvContent = [header, ...rows].join("\n");
        const BOM = "\uFEFF";
        const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });

        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `${selectedDayTitle || 'Schedule'}_Details.csv`);
        link.click();
    };

    const onDragEnd = (result) => {
        const { source, destination, type } = result;
        if (!destination || isDeletionModeActive) return;

        if (type === 'ROW') {
            const newRows = Array.from(scheduleRows);
            const [removed] = newRows.splice(source.index, 1);
            newRows.splice(destination.index, 0, removed);
            setScheduleRows(newRows);
        }
    };

    return (
        <div className="kschedule-container">
            <header className="kschedule-header">
                <h1>🗓️ Schedule Management and Editor</h1>
                {isLoadingDestinations && (
                    <p style={{color: '#007bff'}}>
                        ⏳ 목적지 데이터 불러오는 중...
                    </p>
                )}
            </header>

            {!authError && (
                <>
                    <div className="kschedule-details">
                        <label>Day Title</label>
                        <select
                            className="kschedule-select"
                            value={selectedDayTitle}
                            onChange={handleDayTitleChange}
                        >
                            {dayTitles.map(day => (
                                <option key={day} value={day}>
                                    {day}
                                </option>
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

                    <div className="kschedule-toolbar">
                        <button onClick={handleAddRow} className="kschedule-btn-primary">
                            ➕ Add Row
                        </button>

                        <button
                            onClick={toggleDeletionMode}
                            style={{ background: isDeletionModeActive ? '#ef4444' : '#cc0000', color: 'white' }}
                            className="kschedule-btn-danger"
                        >
                            <Trash2 size={16} />
                            {isDeletionModeActive ? 'Deletion Mode (ON)' : 'Deletion Mode (OFF)'}
                        </button>

                        <button onClick={handleAddColumn} className="kschedule-btn-secondary">
                            ➕ Add Columns
                        </button>
                        <button onClick={handleDownloadCSV} className="kschedule-btn-info">
                            📥 CSV Download
                        </button>
                    </div>

                    <div className="kschedule-table-wrapper">
                        <DragDropContext onDragEnd={onDragEnd}>
                            <table className="kschedule-table">
                                {/* ✅ 열 노래 드래그 제거됨! */}
                                <thead>
                                    <tr>
                                        <th>No.</th>
                                        {scheduleDays.map((day, idx) => (
                                            <th
                                                key={`${day}-${idx}`}
                                                className={isDeletionModeActive ? 'kschedule-column-header-deletable' : ''}
                                                onClick={() => handleRemoveColumn(day)}
                                            >
                                                {day}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>

                                <Droppable droppableId="droppable-rows" type="ROW">
                                    {(provided) => (
                                        <tbody 
                                            ref={provided.innerRef} 
                                            {...provided.droppableProps}
                                        >
                                            {scheduleRows.map((rowItem, ti) => (
                                                <Draggable
                                                    key={rowItem.id}
                                                    draggableId={rowItem.id}
                                                    index={ti}
                                                    isDragDisabled={isDeletionModeActive}
                                                >
                                                    {(provided) => (
                                                        <tr
                                                            ref={provided.innerRef}
                                                            {...provided.draggableProps}
                                                        >
                                                            <td
                                                                className={`kschedule-time-cell ${isDeletionModeActive ? 'kschedule-time-cell-deletable' : ''}`}
                                                                {...provided.dragHandleProps}
                                                                onClick={() => handleRemoveRow(rowItem.id)}
                                                            >
                                                                {ti + 1}
                                                            </td>

                                                            {scheduleDays.map((day, di) => (
                                                                <td key={di} className="kschedule-schedule-cell">
                                                                    <input
                                                                        type="text"
                                                                        value={getCellValue(rowItem.id, day)}
                                                                        onChange={(e) =>
                                                                            handleCellChange(rowItem.id, day, e.target.value)
                                                                        }
                                                                        className="kschedule-cell-input"
                                                                        placeholder=" "
                                                                    />
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    )}
                                                </Draggable>
                                            ))}
                                            {provided.placeholder}
                                        </tbody>
                                    )}
                                </Droppable>
                            </table>
                        </DragDropContext>
                    </div>
                </>
            )}
        </div>
    );
};

export default ScheduleTable;
