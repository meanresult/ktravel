// ktravel/frontend/src/components/dashboard/ReminderWidget.jsx
import React from 'react';
import { Calendar } from 'lucide-react';

const ReminderWidget = ({ reminders }) => {
  return (
    <div className="dashboard-reminder-widget">
      <h3 className="dashboard-widget-header">
        <Calendar size={18} color="#3853FF" />
        취향 리마인드
      </h3>
      {reminders.map((reminder) => (
        <div key={reminder.id} className="dashboard-reminder-card">
          <div className="dashboard-reminder-icon">{reminder.icon}</div>
          <div className="dashboard-reminder-message">{reminder.message}</div>
        </div>
      ))}
    </div>
  );
};

export default ReminderWidget;