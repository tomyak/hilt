import { useRequestStore } from '../../stores/requestStore';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { formatDistanceToNow } from 'date-fns';

const PROVIDER_COLORS = {
  openai: 'bg-blue-500',
  anthropic: 'bg-orange-500',
  gemini: 'bg-purple-500',
};

export function RequestList() {
  const { getPendingRequests, selectRequest, selectedRequestId } = useRequestStore();
  const requests = getPendingRequests();

  if (requests.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pending Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            No pending requests. Waiting for LLM clients...
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pending Requests ({requests.length})</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y">
          {requests.map((request) => (
            <div
              key={request.request_id}
              className={`p-4 cursor-pointer hover:bg-accent transition-colors ${
                selectedRequestId === request.request_id ? 'bg-accent' : ''
              }`}
              onClick={() => selectRequest(request.request_id)}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={PROVIDER_COLORS[request.provider]}>
                      {request.provider}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {request.model}
                    </span>
                  </div>
                  <div className="text-sm font-medium mb-1 truncate">
                    {request.messages[request.messages.length - 1]?.content.substring(0, 60)}...
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(request.timestamp), { addSuffix: true })}
                  </div>
                </div>
                {request.tools && request.tools.length > 0 && (
                  <Badge variant="outline" className="shrink-0">
                    {request.tools.length} tools
                  </Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
