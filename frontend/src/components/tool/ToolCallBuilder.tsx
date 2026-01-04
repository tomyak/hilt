import { useState } from 'react';
import Editor from '@monaco-editor/react';
import { useResponseStore } from '../../stores/responseStore';
import type { Tool, ToolCall } from '../../stores/requestStore';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { X, Plus } from 'lucide-react';

interface ToolCallBuilderProps {
  requestId: string;
  availableTools: Tool[];
}

export function ToolCallBuilder({ requestId, availableTools }: ToolCallBuilderProps) {
  const { getDraft, addToolCall, removeToolCall, updateToolCall } = useResponseStore();
  const [selectedToolName, setSelectedToolName] = useState('');

  const draft = getDraft(requestId);
  const toolCalls = draft?.toolCalls || [];

  const handleAddToolCall = () => {
    if (!selectedToolName) return;

    const tool = availableTools.find((t) => t.function.name === selectedToolName);
    if (!tool) return;

    const newToolCall: ToolCall = {
      id: `call_${Date.now()}`,
      type: 'function',
      function: {
        name: tool.function.name,
        arguments: '{}',
      },
    };

    addToolCall(requestId, newToolCall);
    setSelectedToolName('');
  };

  const handleArgumentsChange = (toolCallId: string, newArgs: string | undefined) => {
    if (newArgs === undefined) return;

    const toolCall = toolCalls.find((tc) => tc.id === toolCallId);
    if (!toolCall) return;

    updateToolCall(requestId, toolCallId, {
      ...toolCall,
      function: {
        ...toolCall.function,
        arguments: newArgs,
      },
    });
  };

  return (
    <div className="space-y-4">
      {/* Add Tool Call */}
      <div className="flex gap-2">
        <select
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          value={selectedToolName}
          onChange={(e) => setSelectedToolName(e.target.value)}
        >
          <option value="">Select a tool...</option>
          {availableTools.map((tool) => (
            <option key={tool.function.name} value={tool.function.name}>
              {tool.function.name} - {tool.function.description}
            </option>
          ))}
        </select>
        <Button
          size="icon"
          onClick={handleAddToolCall}
          disabled={!selectedToolName}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Tool Calls List */}
      {toolCalls.length > 0 && (
        <div className="space-y-3">
          {toolCalls.map((toolCall) => {
            const tool = availableTools.find((t) => t.function.name === toolCall.function.name);
            return (
              <Card key={toolCall.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">{toolCall.function.name}</Badge>
                        <span className="text-xs text-muted-foreground">
                          {tool?.function.description}
                        </span>
                      </div>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => removeToolCall(requestId, toolCall.id)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <div>
                    <div className="text-xs font-semibold mb-1">Arguments (JSON)</div>
                    <Editor
                      height="150px"
                      defaultLanguage="json"
                      value={toolCall.function.arguments}
                      onChange={(value) => handleArgumentsChange(toolCall.id, value)}
                      options={{
                        minimap: { enabled: false },
                        formatOnType: true,
                        formatOnPaste: true,
                        lineNumbers: 'off',
                        scrollBeyondLastLine: false,
                      }}
                      beforeMount={(monaco) => {
                        if (tool) {
                          // Configure JSON schema for intellisense
                          monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
                            validate: true,
                            schemas: [
                              {
                                uri: `http://schema/${tool.function.name}`,
                                fileMatch: ['*'],
                                schema: tool.function.parameters,
                              },
                            ],
                          });
                        }
                      }}
                    />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {toolCalls.length === 0 && (
        <div className="text-center text-sm text-muted-foreground py-4">
          No tool calls added yet
        </div>
      )}
    </div>
  );
}
