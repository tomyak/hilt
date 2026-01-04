import { useState, useEffect, useCallback } from 'react';
import { useRequestStore } from '../../stores/requestStore';
import { useResponseStore } from '../../stores/responseStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { ToolCallBuilder } from '../tool/ToolCallBuilder';

export function ResponseEditor() {
  const { selectedRequestId, getRequest } = useRequestStore();
  const {
    getDraft,
    setDraft,
    getMode,
    setMode,
    clearDraft,
  } = useResponseStore();
  const { send } = useWebSocket();

  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const request = selectedRequestId ? getRequest(selectedRequestId) : null;
  const mode = selectedRequestId ? getMode(selectedRequestId) : 'batch';

  // Load draft when request changes
  useEffect(() => {
    if (selectedRequestId) {
      const draft = getDraft(selectedRequestId);
      setContent(draft?.content || '');
    } else {
      setContent('');
    }
  }, [selectedRequestId, getDraft]);

  // Debounced streaming - send chunks as user types
  useEffect(() => {
    if (!selectedRequestId || mode !== 'streaming') return;

    const timer = setTimeout(() => {
      if (content) {
        send({
          type: 'response_chunk',
          data: {
            request_id: selectedRequestId,
            content: content,
          },
        });
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [content, selectedRequestId, mode, send]);

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setContent(newContent);
    if (selectedRequestId) {
      setDraft(selectedRequestId, newContent);
    }
  };

  const handleModeChange = (newMode: 'streaming' | 'batch') => {
    if (selectedRequestId) {
      setMode(selectedRequestId, newMode);

      if (newMode === 'streaming') {
        send({
          type: 'start_response',
          data: {
            request_id: selectedRequestId,
            mode: 'streaming',
          },
        });
      }
    }
  };

  const handleSubmit = useCallback(() => {
    if (!selectedRequestId || !request) return;

    setIsSubmitting(true);

    const draft = getDraft(selectedRequestId);
    const toolCalls = draft?.toolCalls || [];

    if (mode === 'streaming') {
      // Finish streaming
      send({
        type: 'finish_response',
        data: {
          request_id: selectedRequestId,
          finish_reason: toolCalls.length > 0 ? 'tool_calls' : 'stop',
        },
      });
    } else {
      // Batch mode - send complete response
      send({
        type: 'complete_response',
        data: {
          request_id: selectedRequestId,
          content: content,
          tool_calls: toolCalls.map((tc) => ({
            id: tc.id,
            type: 'function',
            function: {
              name: tc.function.name,
              arguments: tc.function.arguments,
            },
          })),
          finish_reason: toolCalls.length > 0 ? 'tool_calls' : 'stop',
        },
      });
    }

    // Clear draft
    clearDraft(selectedRequestId);
    setContent('');
    setIsSubmitting(false);
  }, [selectedRequestId, request, mode, content, getDraft, send, clearDraft]);

  const handleReject = useCallback(() => {
    if (!selectedRequestId) return;

    send({
      type: 'reject_request',
      data: {
        request_id: selectedRequestId,
        reason: 'rejected',
        message: 'Operator rejected this request',
      },
    });

    clearDraft(selectedRequestId);
    setContent('');
  }, [selectedRequestId, send, clearDraft]);

  if (!selectedRequestId || !request) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-muted-foreground">
            Select a request to compose a response
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Compose Response</CardTitle>
          <div className="flex gap-2">
            <Button
              variant={mode === 'batch' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleModeChange('batch')}
            >
              Batch
            </Button>
            <Button
              variant={mode === 'streaming' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleModeChange('streaming')}
            >
              Streaming
            </Button>
          </div>
        </div>
        {mode === 'streaming' && (
          <Badge variant="outline" className="w-fit mt-2">
            Live streaming - your changes are sent in real-time
          </Badge>
        )}
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-4 overflow-auto">
        {/* Response Content */}
        <div className="flex-1">
          <label htmlFor="response-content" className="text-sm font-semibold mb-2 block">
            Response Content
          </label>
          <Textarea
            id="response-content"
            className="min-h-[200px] font-mono text-sm"
            placeholder="Type your response here..."
            value={content}
            onChange={handleContentChange}
          />
        </div>

        {/* Tool Call Builder */}
        {request.tools && request.tools.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-2">Tool Calls</h3>
            <ToolCallBuilder
              requestId={selectedRequestId}
              availableTools={request.tools}
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 justify-end pt-4 border-t">
          <Button
            variant="outline"
            onClick={handleReject}
            disabled={isSubmitting}
          >
            Reject
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !content.trim()}
          >
            {mode === 'streaming' ? 'Finish Streaming' : 'Submit Response'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
