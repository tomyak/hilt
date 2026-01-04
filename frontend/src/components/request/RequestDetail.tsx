import { useRequestStore } from '../../stores/requestStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';

export function RequestDetail() {
  const { selectedRequestId, getRequest } = useRequestStore();

  if (!selectedRequestId) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-muted-foreground">
            Select a request to view details
          </div>
        </CardContent>
      </Card>
    );
  }

  const request = getRequest(selectedRequestId);

  if (!request) {
    return (
      <Card className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-muted-foreground">
            Request not found
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full overflow-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Request Details</CardTitle>
            <CardDescription className="mt-1">
              {request.model} via {request.provider}
            </CardDescription>
          </div>
          <Badge>{request.provider}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* System Prompt */}
        {request.system && (
          <div>
            <h3 className="text-sm font-semibold mb-2">System Prompt</h3>
            <div className="bg-muted p-3 rounded-md text-sm whitespace-pre-wrap">
              {request.system}
            </div>
          </div>
        )}

        {/* Messages */}
        <div>
          <h3 className="text-sm font-semibold mb-2">Messages</h3>
          <div className="space-y-3">
            {request.messages.map((message, idx) => (
              <div key={idx} className="bg-muted p-3 rounded-md">
                <div className="text-xs font-semibold text-muted-foreground mb-1 uppercase">
                  {message.role}
                </div>
                <div className="text-sm whitespace-pre-wrap">{message.content}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Parameters */}
        <div>
          <h3 className="text-sm font-semibold mb-2">Parameters</h3>
          <div className="bg-muted p-3 rounded-md text-sm font-mono">
            <pre>{JSON.stringify(request.parameters, null, 2)}</pre>
          </div>
        </div>

        {/* Tools */}
        {request.tools && request.tools.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-2">Available Tools ({request.tools.length})</h3>
            <div className="space-y-3">
              {request.tools.map((tool, idx) => (
                <div key={idx} className="bg-muted p-3 rounded-md">
                  <div className="text-sm font-semibold mb-1">{tool.function.name}</div>
                  <div className="text-xs text-muted-foreground mb-2">
                    {tool.function.description}
                  </div>
                  <details className="text-xs">
                    <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                      View parameters schema
                    </summary>
                    <pre className="mt-2 p-2 bg-background rounded">
                      {JSON.stringify(tool.function.parameters, null, 2)}
                    </pre>
                  </details>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
