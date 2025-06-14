import * as React from "react";
import { Check, X, Brain, TrendingUp, AlertTriangle, Clock, ChevronDown, ChevronRight, Building2, Edit3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiClient, type CapabilityRecommendation, type BusinessGoal } from "@/lib/api";
import { toast } from "sonner";
import { useParams } from "react-router-dom";

export function AnalysisPage() {
  const { goalId } = useParams();
  const [recommendations, setRecommendations] = React.useState<CapabilityRecommendation[]>([]);
  const [goals, setGoals] = React.useState<BusinessGoal[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [processingRec, setProcessingRec] = React.useState<string | null>(null);
  const [statusFilter, setStatusFilter] = React.useState<string>("all");
  const [typeFilter, setTypeFilter] = React.useState<string>("all");
  const [goalFilter, setGoalFilter] = React.useState<string>(goalId || "all");

  React.useEffect(() => {
    loadData();
  }, []);

  // Update goalFilter when URL parameter changes
  React.useEffect(() => {
    setGoalFilter(goalId || "all");
  }, [goalId]);

  const loadData = async () => {
    try {
      const [recsResponse, goalsResponse] = await Promise.all([
        apiClient.getRecommendations(),
        apiClient.getBusinessGoals()
      ]);
      setRecommendations(recsResponse.results);
      setGoals(goalsResponse.results);
    } catch (error) {
      toast.error("Failed to load analysis data");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (recommendationId: string) => {
    setProcessingRec(recommendationId);
    try {
      const response = await apiClient.applyRecommendation(recommendationId);
      toast.success(response.message);
      loadData();
    } catch (error) {
      toast.error("Failed to apply recommendation");
      console.error(error);
    } finally {
      setProcessingRec(null);
    }
  };

  const handleReject = async (recommendationId: string) => {
    setProcessingRec(recommendationId);
    try {
      await apiClient.rejectRecommendation(recommendationId);
      toast.success("Recommendation rejected");
      loadData();
    } catch (error) {
      toast.error("Failed to reject recommendation");
      console.error(error);
    } finally {
      setProcessingRec(null);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "ADD_CAPABILITY":
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case "MODIFY_CAPABILITY":
        return <Brain className="h-4 w-4 text-blue-600" />;
      case "DELETE_CAPABILITY":
        return <X className="h-4 w-4 text-red-600" />;
      case "STRENGTHEN_CAPABILITY":
        return <AlertTriangle className="h-4 w-4 text-orange-600" />;
      default:
        return <Brain className="h-4 w-4 text-gray-600" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "ADD_CAPABILITY": return "text-green-600 bg-green-50 border-green-200";
      case "MODIFY_CAPABILITY": return "text-blue-600 bg-blue-50 border-blue-200";
      case "DELETE_CAPABILITY": return "text-red-600 bg-red-50 border-red-200";
      case "STRENGTHEN_CAPABILITY": return "text-orange-600 bg-orange-50 border-orange-200";
      default: return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "PENDING": return "text-yellow-600 bg-yellow-50";
      case "APPLIED": return "text-green-600 bg-green-50";
      case "REJECTED": return "text-red-600 bg-red-50";
      default: return "text-gray-600 bg-gray-50";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatRecommendationType = (type: string) => {
    return type.replace('_', ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
  };

  // Filter recommendations
  const filteredRecommendations = recommendations.filter(rec => {
    if (statusFilter !== "all" && rec.status !== statusFilter) return false;
    if (typeFilter !== "all" && rec.recommendation_type !== typeFilter) return false;
    if (goalFilter !== "all" && rec.business_goal !== goalFilter) return false;
    return true;
  });

  // Group by business goal
  const groupedRecommendations = filteredRecommendations.reduce((acc, rec) => {
    const goalId = rec.business_goal;
    if (!acc[goalId]) {
      acc[goalId] = [];
    }
    acc[goalId].push(rec);
    return acc;
  }, {} as Record<string, CapabilityRecommendation[]>);

  const stats = {
    total: recommendations.length,
    pending: recommendations.filter(r => r.status === "PENDING").length,
    applied: recommendations.filter(r => r.status === "APPLIED").length,
    rejected: recommendations.filter(r => r.status === "REJECTED").length
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center min-h-[400px]">
              <div className="text-center">
                <Progress value={33} className="w-48 mb-4" />
                <p className="text-muted-foreground">Loading analysis data...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Analysis & Recommendations</h1>
        <p className="text-muted-foreground mt-1">
          Review and manage AI-generated capability recommendations from business goal analysis
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-muted-foreground" />
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Total Recommendations</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Pending Review</p>
                <p className="text-2xl font-bold">{stats.pending}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Check className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Applied</p>
                <p className="text-2xl font-bold">{stats.applied}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <X className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-muted-foreground">Rejected</p>
                <p className="text-2xl font-bold">{stats.rejected}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex gap-4">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="APPLIED">Applied</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
              </SelectContent>
            </Select>

            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="ADD_CAPABILITY">Add Capability</SelectItem>
                <SelectItem value="MODIFY_CAPABILITY">Modify Capability</SelectItem>
                <SelectItem value="DELETE_CAPABILITY">Delete Capability</SelectItem>
                <SelectItem value="STRENGTHEN_CAPABILITY">Strengthen Capability</SelectItem>
              </SelectContent>
            </Select>

            <Select value={goalFilter} onValueChange={setGoalFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by goal" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Goals</SelectItem>
                {goals.map((goal) => (
                  <SelectItem key={goal.id} value={goal.id}>
                    {goal.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Tabs defaultValue="grouped" className="w-full">
        <TabsList>
          <TabsTrigger value="grouped">Grouped by Goal</TabsTrigger>
          <TabsTrigger value="list">All Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="grouped" className="space-y-4">
          {Object.entries(groupedRecommendations).length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <Brain className="h-12 w-12 mx-auto mb-4 opacity-50 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No recommendations found</h3>
                <p className="text-muted-foreground">
                  Adjust your filters or analyze more business goals to see recommendations.
                </p>
              </CardContent>
            </Card>
          ) : (
            Object.entries(groupedRecommendations).map(([goalId, goalRecs]) => {
              const goal = goals.find(g => g.id === goalId);
              return (
                <GoalRecommendationsGroup
                  key={goalId}
                  goal={goal}
                  recommendations={goalRecs}
                  onApply={handleApply}
                  onReject={handleReject}
                  processingRec={processingRec}
                  getTypeIcon={getTypeIcon}
                  getTypeColor={getTypeColor}
                  getStatusColor={getStatusColor}
                  formatDate={formatDate}
                  formatRecommendationType={formatRecommendationType}
                />
              );
            })
          )}
        </TabsContent>

        <TabsContent value="list" className="space-y-4">
          {filteredRecommendations.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <Brain className="h-12 w-12 mx-auto mb-4 opacity-50 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No recommendations found</h3>
                <p className="text-muted-foreground">
                  Adjust your filters or analyze more business goals to see recommendations.
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredRecommendations.map((recommendation) => (
              <RecommendationCard
                key={recommendation.id}
                recommendation={recommendation}
                goal={goals.find(g => g.id === recommendation.business_goal)}
                onApply={handleApply}
                onReject={handleReject}
                processingRec={processingRec}
                getTypeIcon={getTypeIcon}
                getTypeColor={getTypeColor}
                getStatusColor={getStatusColor}
                formatDate={formatDate}
                formatRecommendationType={formatRecommendationType}
              />
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface GoalRecommendationsGroupProps {
  goal?: BusinessGoal;
  recommendations: CapabilityRecommendation[];
  onApply: (id: string) => void;
  onReject: (id: string) => void;
  processingRec: string | null;
  getTypeIcon: (type: string) => React.ReactNode;
  getTypeColor: (type: string) => string;
  getStatusColor: (status: string) => string;
  formatDate: (date: string) => string;
  formatRecommendationType: (type: string) => string;
}

function GoalRecommendationsGroup({
  goal,
  recommendations,
  onApply,
  onReject,
  processingRec,
  getTypeIcon,
  getTypeColor,
  getStatusColor,
  formatDate,
  formatRecommendationType
}: GoalRecommendationsGroupProps) {
  const [expanded, setExpanded] = React.useState(true);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="p-0 h-auto"
            >
              {expanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
            <div>
              <CardTitle className="text-lg">
                {goal?.title || "Unknown Goal"}
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                {recommendations.length} recommendation{recommendations.length !== 1 ? 's' : ''} • 
                {recommendations.filter(r => r.status === "PENDING").length} pending
              </p>
            </div>
          </div>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0">
          <div className="space-y-3">
            {recommendations.map((recommendation) => (
              <RecommendationCard
                key={recommendation.id}
                recommendation={recommendation}
                goal={goal}
                onApply={onApply}
                onReject={onReject}
                processingRec={processingRec}
                getTypeIcon={getTypeIcon}
                getTypeColor={getTypeColor}
                getStatusColor={getStatusColor}
                formatDate={formatDate}
                formatRecommendationType={formatRecommendationType}
              />
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

interface RecommendationCardProps {
  recommendation: CapabilityRecommendation;
  goal?: BusinessGoal;
  onApply: (id: string) => void;
  onReject: (id: string) => void;
  processingRec: string | null;
  getTypeIcon: (type: string) => React.ReactNode;
  getTypeColor: (type: string) => string;
  getStatusColor: (status: string) => string;
  formatDate: (date: string) => string;
  formatRecommendationType: (type: string) => string;
  compact?: boolean;
}

function RecommendationCard({
  recommendation,
  goal,
  onApply,
  onReject,
  processingRec,
  getTypeIcon,
  getTypeColor,
  getStatusColor,
  formatDate,
  formatRecommendationType,
  compact = false
}: RecommendationCardProps) {
  const [showDetails, setShowDetails] = React.useState(false);

  // Calculate the predicted level for ADD_CAPABILITY recommendations
  const getPredictedLevel = () => {
    if (recommendation.recommendation_type === 'ADD_CAPABILITY') {
      if (recommendation.proposed_parent_details) {
        return recommendation.proposed_parent_details.level + 1;
      } else {
        return 1; // Top-level capability
      }
    }
    return null;
  };

  // Get level styling based on predicted level
  const getLevelStyling = (level: number) => {
    switch (level) {
      case 1:
        return {
          badge: "bg-primary text-primary-foreground",
          border: "border-primary/30",
          bg: "bg-primary/5"
        };
      case 2:
        return {
          badge: "bg-blue-500 text-white",
          border: "border-blue-400/30",
          bg: "bg-blue-50/50"
        };
      case 3:
        return {
          badge: "bg-green-500 text-white",
          border: "border-green-400/30",
          bg: "bg-green-50/50"
        };
      default:
        return {
          badge: "bg-gray-500 text-white",
          border: "border-gray-400/30",
          bg: "bg-gray-50/50"
        };
    }
  };

  const predictedLevel = getPredictedLevel();
  const levelStyling = predictedLevel ? getLevelStyling(predictedLevel) : null;

  return (
    <Card className={compact ? "border-l-4" : ""} style={compact ? { borderLeftColor: getTypeColor(recommendation.recommendation_type).split(' ')[0] } : {}}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              {getTypeIcon(recommendation.recommendation_type)}
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getTypeColor(recommendation.recommendation_type)}`}>
                {formatRecommendationType(recommendation.recommendation_type)}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(recommendation.status)}`}>
                {recommendation.status}
              </span>
              {recommendation.confidence_score && (
                <span className="text-xs text-muted-foreground">
                  {Math.round(recommendation.confidence_score * 100)}% confidence
                </span>
              )}
              {/* Show predicted level for new capabilities */}
              {predictedLevel && (
                <span className={`text-xs px-2 py-1 rounded font-medium ${levelStyling?.badge}`}>
                  Level {predictedLevel}
                </span>
              )}
            </div>

            <h4 className="font-semibold text-base">
              {recommendation.proposed_name || recommendation.target_capability_details?.name || "Capability Update"}
            </h4>

            {/* Enhanced hierarchy preview for ADD_CAPABILITY */}
            {recommendation.recommendation_type === 'ADD_CAPABILITY' && recommendation.proposed_parent_details && (
              <div className={`mt-3 p-3 rounded-lg border ${levelStyling?.border} ${levelStyling?.bg}`}>
                <div className="flex items-center gap-2 text-sm text-gray-700 mb-2">
                  <Building2 className="h-4 w-4" />
                  <span className="font-medium">Will be placed under:</span>
                </div>
                <div className="text-sm space-y-1">
                  <div className="font-medium text-gray-900">
                    {recommendation.proposed_parent_details.full_path}
                  </div>
                  <div className="text-xs text-gray-600">
                    Hierarchy: {recommendation.proposed_parent_details.full_path} → <span className="font-medium text-gray-900">{recommendation.proposed_name}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span>Parent Level: {recommendation.proposed_parent_details.level}</span>
                    <span>•</span>
                    <span className="font-medium">New Level: {predictedLevel}</span>
                  </div>
                  {/* Compact hierarchy preview */}
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <div className="text-xs text-gray-500 mb-1">Quick Preview:</div>
                    <div className="flex items-center gap-1 text-xs">
                      {recommendation.proposed_parent_details.full_path.split(' > ').map((part: string, index: number, array: string[]) => (
                        <React.Fragment key={index}>
                          <span className="text-gray-500">{part}</span>
                          {index < array.length - 1 && <span className="text-gray-400">→</span>}
                        </React.Fragment>
                      ))}
                      <span className="text-gray-400">→</span>
                      <span className="font-medium text-primary bg-primary/10 px-1 rounded">{recommendation.proposed_name}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* For top-level capabilities */}
            {recommendation.recommendation_type === 'ADD_CAPABILITY' && !recommendation.proposed_parent_details && (
              <div className={`mt-3 p-3 rounded-lg border ${levelStyling?.border} ${levelStyling?.bg}`}>
                <div className="flex items-center gap-2 text-sm text-gray-700 mb-2">
                  <Building2 className="h-4 w-4" />
                  <span className="font-medium">Will be created as:</span>
                </div>
                <div className="text-sm">
                  <div className="font-medium text-gray-900">Top-Level Capability (Level 1)</div>
                  <div className="text-xs text-gray-600 mt-1">
                    This will be a root capability in your business architecture
                  </div>
                  {/* Compact preview for root capability */}
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <div className="text-xs text-gray-500 mb-1">Quick Preview:</div>
                    <div className="flex items-center gap-1 text-xs">
                      <span className="font-medium text-primary bg-primary/10 px-1 rounded">{recommendation.proposed_name}</span>
                      <span className="text-gray-500">(Root Level)</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Enhanced info for MODIFY_CAPABILITY */}
            {recommendation.recommendation_type === 'MODIFY_CAPABILITY' && recommendation.target_capability_details && (
              <div className="mt-3 p-3 rounded-lg border border-blue-200 bg-blue-50/30">
                <div className="flex items-center gap-2 text-sm text-blue-700 mb-2">
                  <Edit3 className="h-4 w-4" />
                  <span className="font-medium">Will modify existing capability:</span>
                </div>
                <div className="text-sm">
                  <div className="font-medium text-blue-900">
                    {recommendation.target_capability_details.full_path}
                  </div>
                  <div className="text-xs text-blue-600 mt-1">
                    Current Level: {recommendation.target_capability_details.level}
                    {recommendation.proposed_parent_details && (
                      <span> → New Parent: {recommendation.proposed_parent_details.name}</span>
                    )}
                  </div>
                </div>
              </div>
            )}

            {!compact && goal && (
              <p className="text-sm text-muted-foreground mt-2">
                For goal: {goal.title}
              </p>
            )}

            <p className="text-xs text-muted-foreground mt-1">
              Recommended {formatDate(recommendation.recommended_by_ai_at)}
            </p>
          </div>

          <div className="flex gap-2 ml-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? "Hide" : "Show"} Details
            </Button>

            {recommendation.status === "PENDING" && (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onReject(recommendation.id)}
                  disabled={processingRec === recommendation.id}
                  className="text-red-600 hover:text-red-700"
                >
                  <X className="h-4 w-4 mr-1" />
                  Reject
                </Button>
                <Button
                  size="sm"
                  onClick={() => onApply(recommendation.id)}
                  disabled={processingRec === recommendation.id}
                >
                  {processingRec === recommendation.id ? (
                    <>
                      <Clock className="h-4 w-4 mr-1 animate-spin" />
                      Applying...
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-1" />
                      Apply
                    </>
                  )}
                </Button>
              </>
            )}
          </div>
        </div>
      </CardHeader>

      {showDetails && (
        <CardContent className="pt-0">
          <div className="space-y-4">
            {recommendation.proposed_description && (
              <div>
                <h5 className="text-sm font-medium mb-1">Description</h5>
                <p className="text-sm text-muted-foreground">
                  {recommendation.proposed_description}
                </p>
              </div>
            )}

            {recommendation.additional_details && (
              <div>
                <h5 className="text-sm font-medium mb-1">AI Rationale</h5>
                <p className="text-sm text-muted-foreground">
                  {recommendation.additional_details}
                </p>
              </div>
            )}

            {/* Enhanced details section */}
            {recommendation.recommendation_type === 'ADD_CAPABILITY' && (
              <div>
                <h5 className="text-sm font-medium mb-2">Placement Details</h5>
                <div className="space-y-3">
                  {/* Detailed placement info */}
                  <div className="space-y-2 text-sm text-muted-foreground">
                    {recommendation.proposed_parent_details ? (
                      <>
                        <div className="flex justify-between">
                          <span>Parent Capability:</span>
                          <span className="font-medium">{recommendation.proposed_parent_details.name}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Full Hierarchy:</span>
                          <span className="font-medium">{recommendation.proposed_parent_details.full_path} → {recommendation.proposed_name}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Will be at Level:</span>
                          <span className="font-medium">{predictedLevel}</span>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="flex justify-between">
                          <span>Position:</span>
                          <span className="font-medium">Top-Level (Root)</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Level:</span>
                          <span className="font-medium">1</span>
                        </div>
                      </>
                    )}
                  </div>
                  
                  {/* Visual hierarchy preview */}
                  <div>
                    <h6 className="text-xs font-medium text-gray-700 mb-2 uppercase tracking-wide">Hierarchy Preview</h6>
                    <div className="bg-gray-50 border rounded-lg p-3">
                      <HierarchyPreview
                        parentPath={recommendation.proposed_parent_details?.full_path}
                        newCapabilityName={recommendation.proposed_name || 'New Capability'}
                        level={predictedLevel || 1}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {recommendation.target_capability_details && (
              <div>
                <h5 className="text-sm font-medium mb-1">Target Capability</h5>
                <p className="text-sm text-muted-foreground">
                  {recommendation.target_capability_details.full_path}
                </p>
              </div>
            )}

            {recommendation.proposed_parent_details && recommendation.recommendation_type !== 'ADD_CAPABILITY' && (
              <div>
                <h5 className="text-sm font-medium mb-1">Proposed Parent</h5>
                <p className="text-sm text-muted-foreground">
                  {recommendation.proposed_parent_details.full_path}
                </p>
              </div>
            )}

            {recommendation.status === "APPLIED" && recommendation.applied_at && (
              <Alert>
                <Check className="h-4 w-4" />
                <AlertDescription>
                  Applied on {formatDate(recommendation.applied_at)}
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// Helper component to show hierarchy preview
interface HierarchyPreviewProps {
  parentPath?: string;
  newCapabilityName: string;
  level: number;
}

function HierarchyPreview({ parentPath, newCapabilityName, level }: HierarchyPreviewProps) {
  if (!parentPath) {
    return (
      <div className="flex items-center text-sm">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-primary rounded-full"></div>
          <span className="font-medium text-primary">{newCapabilityName}</span>
          <span className="text-xs text-gray-500">(Level 1)</span>
        </div>
      </div>
    );
  }

  const pathParts = parentPath.split(' > ');
  
  return (
    <div className="space-y-1 text-sm">
      {pathParts.map((part, index) => (
        <div key={index} className="flex items-center" style={{ paddingLeft: `${index * 16}px` }}>
          <div className="flex items-center gap-2">
            <div className="w-1 h-4 bg-gray-300"></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
            <span className="text-gray-600">{part}</span>
            <span className="text-xs text-gray-400">(L{index + 1})</span>
          </div>
        </div>
      ))}
      {/* New capability */}
      <div className="flex items-center" style={{ paddingLeft: `${pathParts.length * 16}px` }}>
        <div className="flex items-center gap-2">
          <div className="w-1 h-4 bg-primary"></div>
          <div className="w-2 h-2 bg-primary rounded-full"></div>
          <span className="font-medium text-primary">{newCapabilityName}</span>
          <span className="text-xs text-primary">(L{level})</span>
          <span className="text-xs bg-green-100 text-green-700 px-1 rounded">NEW</span>
        </div>
      </div>
    </div>
  );
} 