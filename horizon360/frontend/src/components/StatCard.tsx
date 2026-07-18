import React from 'react';

interface StatCardProps {
  title: string;
  value: string;
  subtext: string;
  subtextHighlight?: string;
  isPositive?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({ title, value, subtext, subtextHighlight, isPositive }) => (
  <div className="bg-white p-5 border-r border-b border-t first:border-l border-gray-200 first:rounded-l-lg last:rounded-r-lg">
    <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{title}</h3>
    <p className="text-4xl font-bold text-gray-900 mt-2 tracking-tight">{value}</p>
    <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
      {subtextHighlight && (
        <span className={isPositive ? 'text-green-500' : 'text-yellow-600'}>
          {isPositive ? '↗' : ''} {subtextHighlight}
        </span>
      )}
      {subtext}
    </p>
  </div>
);
