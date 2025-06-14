import { Badge } from "./badge";
import { Progress } from "./progress";
import { cn } from "@/lib/utils";

interface SimilarityIndicatorProps {
  score: number;
  className?: string;
  showProgress?: boolean;
  showBadge?: boolean;
}

export function SimilarityIndicator({ 
  score, 
  className,
  showProgress = true,
  showBadge = true
}: SimilarityIndicatorProps) {
  const percentage = Math.round(score * 100);
  
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreVariant = (score: number) => {
    if (score >= 0.8) return "default";
    if (score >= 0.6) return "secondary";
    return "destructive";
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {showProgress && (
        <div className="flex-1 min-w-[60px]">
          <Progress value={percentage} className="h-2" />
        </div>
      )}
      
      {showBadge && (
        <Badge variant={getScoreVariant(score)} className="text-xs font-medium">
          {percentage}%
        </Badge>
      )}
      
      {!showBadge && (
        <span className={cn("text-sm font-medium", getScoreColor(score))}>
          {percentage}%
        </span>
      )}
    </div>
  );
} 