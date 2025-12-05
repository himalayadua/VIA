/**
 * SettingsModal Component
 * 
 * Modal dialog for configuring chat settings including model selection,
 * API key, temperature, and max tokens.
 */

import { useState, useEffect } from 'react';
import { X, Eye, EyeOff, AlertCircle, Settings as SettingsIcon } from 'lucide-react';

export interface ChatSettings {
  model: string;
  apiKey: string;
  temperature: number;
  maxTokens: number;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentSettings: ChatSettings;
  onSave: (settings: ChatSettings) => void;
}

interface ModelOption {
  id: string;
  name: string;
  provider: string;
}

const NVIDIA_NIM_MODELS: ModelOption[] = [
  { id: 'google/gemma-3-27b-it', name: 'Gemma 3 27B', provider: 'Google' },
  { id: 'qwen/qwen3-next-80b-a3b-instruct', name: 'Qwen3 Next 80B', provider: 'Qwen' },
  { id: 'openai/gpt-oss-20b', name: 'GPT OSS 20B', provider: 'OpenAI' },
  { id: 'openai/gpt-oss-120b', name: 'GPT OSS 120B', provider: 'OpenAI' },
  { id: 'qwen/qwen3-coder-480b-a35b-instruct', name: 'Qwen3 Coder 480B', provider: 'Qwen' },
  { id: 'nvidia/llama-3.3-nemotron-super-49b-v1.5', name: 'Nemotron Super 49B', provider: 'NVIDIA' },
  { id: 'deepseek-ai/deepseek-v3.1', name: 'DeepSeek V3.1', provider: 'DeepSeek' },
  { id: 'nvidia/llama-3.1-nemotron-ultra-253b-v1', name: 'Nemotron Ultra 253B', provider: 'NVIDIA' },
  { id: 'meta/llama-3.3-70b-instruct', name: 'Llama 3.3 70B', provider: 'Meta' }
];

export const SettingsModal = ({ isOpen, onClose, currentSettings, onSave }: SettingsModalProps) => {
  const [settings, setSettings] = useState<ChatSettings>(currentSettings);
  const [showApiKey, setShowApiKey] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Update local state when currentSettings change
  useEffect(() => {
    setSettings(currentSettings);
  }, [currentSettings]);

  // Get selected model info
  const selectedModel = NVIDIA_NIM_MODELS.find(m => m.id === settings.model);

  const handleModelChange = (newModel: string) => {
    setSettings(prev => ({
      ...prev,
      model: newModel,
      // Don't clear API key - user might have it saved
    }));
    setError(null);
  };

  const validateApiKey = (key: string): boolean => {
    // NVIDIA NIM keys typically start with "nvapi-"
    return key.trim().length > 0 && (key.startsWith('nvapi-') || key.startsWith('sk-'));
  };

  const handleSave = () => {
    // Validate API key
    if (!settings.apiKey.trim()) {
      setError('API key is required');
      return;
    }

    if (!validateApiKey(settings.apiKey)) {
      setError('Invalid API key format. Should start with "nvapi-" or "sk-"');
      return;
    }

    // Validate temperature
    if (settings.temperature < 0 || settings.temperature > 2) {
      setError('Temperature must be between 0.0 and 2.0');
      return;
    }

    // Validate max tokens
    if (settings.maxTokens < 256 || settings.maxTokens > 4096) {
      setError('Max tokens must be between 256 and 4096');
      return;
    }

    onSave(settings);
    onClose();
  };

  const handleCancel = () => {
    setSettings(currentSettings);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <div className="bg-slate-900 rounded-lg shadow-2xl w-full max-w-md max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <SettingsIcon className="w-5 h-5 text-blue-500" aria-hidden="true" />
            <h2 id="settings-title" className="text-xl font-bold text-slate-100">Chat Settings</h2>
          </div>
          <button
            onClick={handleCancel}
            className="p-2 hover:bg-slate-800 rounded transition-colors"
            aria-label="Close settings"
          >
            <X className="w-5 h-5 text-slate-400" aria-hidden="true" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Security Warning */}
          <div className="bg-amber-900/20 border border-amber-800 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-amber-400">
                <p className="font-medium mb-1">Security Notice</p>
                <p>API keys are stored in your browser's local storage. Only use this on trusted devices.</p>
              </div>
            </div>
          </div>

          {/* Model Selection */}
          <div className="space-y-2">
            <label htmlFor="model-select" className="text-sm font-medium text-slate-300">Model</label>
            <select
              id="model-select"
              value={settings.model}
              onChange={(e) => handleModelChange(e.target.value)}
              className="w-full bg-slate-800 text-slate-100 rounded-lg px-3 py-2.5 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-describedby="model-hint"
            >
              {NVIDIA_NIM_MODELS.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name} ({model.provider})
                </option>
              ))}
            </select>
            <p className="text-xs text-slate-500">
              Select the NVIDIA NIM model to use for chat
            </p>
          </div>

          {/* API Key Input */}
          <div className="space-y-2">
            <label htmlFor="api-key-input" className="text-sm font-medium text-slate-300">
              API Key for {selectedModel?.name || 'Selected Model'}
            </label>
            <div className="relative">
              <input
                id="api-key-input"
                type={showApiKey ? 'text' : 'password'}
                value={settings.apiKey}
                onChange={(e) => {
                  setSettings({ ...settings, apiKey: e.target.value });
                  setError(null);
                }}
                placeholder="nvapi-xxxxxxxxxxxxx"
                className="w-full bg-slate-800 text-slate-100 rounded-lg px-3 py-2.5 pr-10 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                aria-describedby="api-key-hint"
                aria-required="true"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300"
                aria-label={showApiKey ? 'Hide API key' : 'Show API key'}
              >
                {showApiKey ? <EyeOff className="w-4 h-4" aria-hidden="true" /> : <Eye className="w-4 h-4" aria-hidden="true" />}
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Each model requires its own NVIDIA NIM API key
            </p>
            {!settings.apiKey && (
              <p className="text-xs text-amber-500 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                API key required for this model
              </p>
            )}
          </div>

          {/* Temperature Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-medium text-slate-300">Temperature</label>
              <span className="text-sm text-slate-400 font-mono">{settings.temperature.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
              style={{
                background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(settings.temperature / 2) * 100}%, #334155 ${(settings.temperature / 2) * 100}%, #334155 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-slate-500">
              <span>Focused (0.0)</span>
              <span>Balanced (1.0)</span>
              <span>Creative (2.0)</span>
            </div>
            <p className="text-xs text-slate-500">
              Controls randomness. Lower = more focused, Higher = more creative
            </p>
          </div>

          {/* Max Tokens Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Max Tokens</label>
            <input
              type="number"
              min="256"
              max="4096"
              step="256"
              value={settings.maxTokens}
              onChange={(e) => setSettings({ ...settings, maxTokens: parseInt(e.target.value) || 256 })}
              className="w-full bg-slate-800 text-slate-100 rounded-lg px-3 py-2.5 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-slate-500">
              Maximum length of response (256-4096)
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-slate-700">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-slate-300 hover:text-slate-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!settings.apiKey}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};
