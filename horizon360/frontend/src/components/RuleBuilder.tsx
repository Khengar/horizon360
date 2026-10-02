import React from 'react';
import { Plus, X, Trash2 } from 'lucide-react';

export interface RuleNode {
  type: 'group' | 'condition';
  logic?: 'AND' | 'OR';
  rules?: RuleNode[];
  field?: string;
  operator?: string;
  value?: string;
}

interface RuleBuilderProps {
  ruleTree: RuleNode;
  onChange: (newTree: RuleNode) => void;
}

export const RuleBuilder: React.FC<RuleBuilderProps> = ({ ruleTree, onChange }) => {
  return (
    <div className="bg-white border border-gray-200 rounded p-4 text-sm font-sans w-full">
      <RuleGroup node={ruleTree} onChange={onChange} isRoot={true} />
    </div>
  );
};

const RuleGroup = ({ node, onChange, isRoot = false }: { node: RuleNode, onChange: (n: RuleNode) => void, isRoot?: boolean }) => {
  const handleLogicChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({ ...node, logic: e.target.value as 'AND' | 'OR' });
  };

  const addCondition = () => {
    const newRules = [...(node.rules || []), { type: 'condition', field: '', operator: '==', value: '' } as RuleNode];
    onChange({ ...node, rules: newRules });
  };

  const addGroup = () => {
    const newRules = [...(node.rules || []), { type: 'group', logic: 'AND', rules: [] } as RuleNode];
    onChange({ ...node, rules: newRules });
  };

  const updateRule = (index: number, updatedRule: RuleNode) => {
    const newRules = [...(node.rules || [])];
    newRules[index] = updatedRule;
    onChange({ ...node, rules: newRules });
  };

  const removeRule = (index: number) => {
    const newRules = [...(node.rules || [])];
    newRules.splice(index, 1);
    onChange({ ...node, rules: newRules });
  };

  return (
    <div className={`relative ${!isRoot ? 'ml-2 pl-3 border-l-2 border-indigo-200 mt-2' : ''}`}>
      <div className="flex items-center space-x-2 mb-3">
        <select 
          className="bg-indigo-50 border border-indigo-200 text-indigo-700 rounded px-2 py-1 text-xs font-bold focus:ring-0 focus:outline-none"
          value={node.logic} 
          onChange={handleLogicChange}
        >
          <option value="AND">AND</option>
          <option value="OR">OR</option>
        </select>
        
        <button onClick={addCondition} className="flex items-center text-xs text-gray-600 hover:text-indigo-600 bg-gray-100 hover:bg-indigo-50 px-2 py-1 rounded transition-colors">
          <Plus size={12} className="mr-1" /> Rule
        </button>
        <button onClick={addGroup} className="flex items-center text-xs text-gray-600 hover:text-indigo-600 bg-gray-100 hover:bg-indigo-50 px-2 py-1 rounded transition-colors">
          <Plus size={12} className="mr-1" /> Group
        </button>
        
        {!isRoot && (
          <button onClick={() => onChange({ type: 'delete_me' } as any)} className="ml-auto text-red-400 hover:text-red-600 p-1">
            <X size={14} />
          </button>
        )}
      </div>

      <div className="space-y-2">
        {(node.rules || []).map((rule, idx) => (
          <div key={idx}>
            {rule.type === 'group' ? (
              <RuleGroup 
                node={rule} 
                onChange={(updated) => {
                  if ((updated as any).type === 'delete_me') removeRule(idx);
                  else updateRule(idx, updated);
                }} 
              />
            ) : (
              <RuleCondition 
                rule={rule} 
                onChange={(updated) => updateRule(idx, updated)}
                onRemove={() => removeRule(idx)} 
              />
            )}
          </div>
        ))}
        {(!node.rules || node.rules.length === 0) && (
          <div className="text-gray-400 text-xs italic py-1">No rules defined.</div>
        )}
      </div>
    </div>
  );
};

const RuleCondition = ({ rule, onChange, onRemove }: { rule: RuleNode, onChange: (r: RuleNode) => void, onRemove: () => void }) => {
  return (
    <div className="flex items-center space-x-1 bg-gray-50 border border-gray-200 p-1.5 rounded w-full">
      <input 
        type="text" 
        className="w-1/3 border border-gray-300 rounded px-1.5 py-1 text-[10px] font-mono focus:ring-1 focus:ring-indigo-500 focus:outline-none"
        placeholder="trigger.payload.amount"
        value={rule.field || ''}
        onChange={(e) => onChange({ ...rule, field: e.target.value })}
      />
      <select 
        className="w-1/4 border border-gray-300 rounded px-1 py-1 text-[10px] font-mono bg-white focus:ring-1 focus:ring-indigo-500 focus:outline-none"
        value={rule.operator || '=='}
        onChange={(e) => onChange({ ...rule, operator: e.target.value })}
      >
        <option value="==">==</option>
        <option value="!=">!=</option>
        <option value=">">&gt;</option>
        <option value="<">&lt;</option>
        <option value=">=">&gt;=</option>
        <option value="<=">&lt;=</option>
        <option value="contains">Contains</option>
      </select>
      <input 
        type="text" 
        className="w-1/3 border border-gray-300 rounded px-1.5 py-1 text-[10px] font-mono focus:ring-1 focus:ring-indigo-500 focus:outline-none"
        placeholder="1000"
        value={rule.value || ''}
        onChange={(e) => onChange({ ...rule, value: e.target.value })}
      />
      <button onClick={onRemove} className="text-gray-400 hover:text-red-500 p-1 flex-shrink-0">
        <Trash2 size={12} />
      </button>
    </div>
  );
};
