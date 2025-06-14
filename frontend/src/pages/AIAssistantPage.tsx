import * as React from "react";
import { Send, Bot, User, Brain, Loader2, Lightbulb } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SimilarityIndicator } from "@/components/ui/similarity-indicator";
import { apiClient, type LLMResponse } from "@/lib/api";
import { toast } from "sonner";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  vectorContext?: {
    similar_capabilities: any[];
    similar_goals: any[];
    similar_recommendations: any[];
    context_enhancement: string;
  };
}

export function AIAssistantPage() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const scrollAreaRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    // Scroll to bottom when new messages are added
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response: LLMResponse = await apiClient.queryLLM({
        query: userMessage.content
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        timestamp: new Date(),
        vectorContext: response.vector_context
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      toast.error("Failed to get AI response");
      console.error(error);
      
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "I apologize, but I'm having trouble processing your request right now. Please try again later.",
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const suggestedQuestions = [
    "What are our most critical capabilities that need strengthening?",
    "How can we improve our digital transformation capabilities?",
    "What capability gaps do we have in customer experience?",
    "Which capabilities should we prioritize for investment?",
    "How do our current capabilities align with industry best practices?"
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] space-y-4">
      {/* Header */}
      <div className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">AI Assistant</h1>
            <p className="text-muted-foreground mt-1">
              Ask questions about your business capabilities and get AI-powered insights
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Brain className="h-4 w-4" />
            <span>Vector-Enhanced AI</span>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <Card className="flex-1 flex flex-col">
        <CardHeader className="flex-shrink-0 pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Chat History
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col p-0">
          <ScrollArea className="flex-1 p-6" ref={scrollAreaRef}>
            <div className="space-y-6">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <Bot className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
                  <p className="text-muted-foreground mb-6">
                    Ask me anything about your business capabilities, goals, or recommendations.
                  </p>
                  
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-muted-foreground">Try asking:</p>
                    <div className="grid gap-2">
                      {suggestedQuestions.map((question, index) => (
                        <Button
                          key={index}
                          variant="outline"
                          size="sm"
                          className="text-left h-auto p-3 justify-start"
                          onClick={() => setInput(question)}
                        >
                          <Lightbulb className="h-4 w-4 mr-2 flex-shrink-0" />
                          <span className="text-sm">{question}</span>
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <ChatMessageComponent
                    key={message.id}
                    message={message}
                    formatTime={formatTime}
                  />
                ))
              )}

              {isLoading && (
                <div className="flex items-start gap-3">
                  <Bot className="h-8 w-8 p-1 bg-primary text-primary-foreground rounded-full flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium">AI Assistant</span>
                      <span className="text-xs text-muted-foreground">
                        {formatTime(new Date())}
                      </span>
                    </div>
                    <Card className="p-4">
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm text-muted-foreground">
                          Analyzing your question and searching for relevant context...
                        </span>
                      </div>
                    </Card>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t p-4">
            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="flex gap-3">
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask me about your business capabilities, goals, or strategy..."
                  className="flex-1 min-h-[80px] resize-none"
                  disabled={isLoading}
                />
                <Button 
                  type="submit" 
                  disabled={!input.trim() || isLoading}
                  className="self-end"
                  size="lg"
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Press Enter to send, Shift+Enter for new line. 
                Your questions will be enhanced with relevant context from your capability map.
              </p>
            </form>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface ChatMessageComponentProps {
  message: ChatMessage;
  formatTime: (date: Date) => string;
}

function ChatMessageComponent({ message, formatTime }: ChatMessageComponentProps) {
  const [showContext, setShowContext] = React.useState(false);

  return (
    <div className="flex items-start gap-3">
      {message.role === "user" ? (
        <User className="h-8 w-8 p-1 bg-muted rounded-full flex-shrink-0 mt-1" />
      ) : (
        <Bot className="h-8 w-8 p-1 bg-primary text-primary-foreground rounded-full flex-shrink-0 mt-1" />
      )}
      
      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <span className="font-medium">
            {message.role === "user" ? "You" : "AI Assistant"}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatTime(message.timestamp)}
          </span>
          {message.vectorContext && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowContext(!showContext)}
              className="text-xs h-6 px-2"
            >
              <Brain className="h-3 w-3 mr-1" />
              {showContext ? "Hide" : "Show"} Context
            </Button>
          )}
        </div>
        
        <Card className="p-4">
          <div className="prose prose-sm max-w-none">
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {message.content}
            </div>
          </div>
        </Card>

        {message.vectorContext && showContext && (
          <div className="space-y-3 mt-3">
            <Alert>
              <Brain className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-3">
                  <div>
                    <span className="font-medium">Context Enhancement:</span>
                    <p className="text-sm mt-1">{message.vectorContext.context_enhancement}</p>
                  </div>
                  
                  {message.vectorContext.similar_capabilities.length > 0 && (
                    <div>
                      <span className="font-medium">Related Capabilities:</span>
                      <div className="space-y-2 mt-2">
                        {message.vectorContext.similar_capabilities.map((cap, index) => (
                          <div key={index} className="flex items-center justify-between bg-muted p-2 rounded">
                            <div>
                              <span className="font-medium text-sm">{cap.name}</span>
                              <p className="text-xs text-muted-foreground">{cap.relevance}</p>
                            </div>
                            <SimilarityIndicator score={cap.similarity_score} showProgress={false} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {message.vectorContext.similar_goals.length > 0 && (
                    <div>
                      <span className="font-medium">Similar Past Goals:</span>
                      <div className="space-y-2 mt-2">
                        {message.vectorContext.similar_goals.map((goal, index) => (
                          <div key={index} className="flex items-center justify-between bg-muted p-2 rounded">
                            <div>
                              <span className="font-medium text-sm">{goal.title}</span>
                              <p className="text-xs text-muted-foreground">{goal.outcome}</p>
                            </div>
                            <SimilarityIndicator score={goal.similarity_score} showProgress={false} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          </div>
        )}
      </div>
    </div>
  );
} 