import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { RequestList } from '../components/request/RequestList';
import { RequestDetail } from '../components/request/RequestDetail';
import { ResponseEditor } from '../components/response/ResponseEditor';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { LogOut } from 'lucide-react';

export function DashboardPage() {
  const { username, logout } = useAuthStore();
  const { isConnected } = useWebSocket();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-muted/30">
      {/* Header */}
      <header className="border-b bg-background">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">HILT</h1>
            <Badge variant={isConnected ? 'default' : 'destructive'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              {username}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)]">
          {/* Request List - Left Column */}
          <div className="col-span-3 overflow-auto">
            <RequestList />
          </div>

          {/* Request Detail - Middle Column */}
          <div className="col-span-4 overflow-auto">
            <RequestDetail />
          </div>

          {/* Response Editor - Right Column */}
          <div className="col-span-5 overflow-auto">
            <ResponseEditor />
          </div>
        </div>
      </main>
    </div>
  );
}
