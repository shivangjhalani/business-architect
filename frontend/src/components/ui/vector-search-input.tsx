import * as React from "react";
import { Search, Loader2 } from "lucide-react";
import { Input } from "./input";
import { Button } from "./button";
import { cn } from "@/lib/utils";

interface VectorSearchInputProps {
  placeholder?: string;
  onSearch: (query: string) => void;
  isLoading?: boolean;
  className?: string;
  autoFocus?: boolean;
}

export function VectorSearchInput({
  placeholder = "Search using AI semantic matching...",
  onSearch,
  isLoading = false,
  className,
  autoFocus = false
}: VectorSearchInputProps) {
  const [query, setQuery] = React.useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={cn("relative flex gap-2", className)}>
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="pl-10 pr-4"
          autoFocus={autoFocus}
          disabled={isLoading}
        />
      </div>
      <Button 
        type="submit" 
        disabled={!query.trim() || isLoading}
        size="default"
        className="shrink-0"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            Searching...
          </>
        ) : (
          "Search"
        )}
      </Button>
    </form>
  );
} 